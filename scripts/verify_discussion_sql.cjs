/* Run against disposable WASM PostgreSQL. Usage: node script.cjs <external npm package directory> */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");
const { createHash } = require("node:crypto");
const external = createRequire(path.resolve(process.argv[2], "package.json"));
const { PGlite } = external("@electric-sql/pglite");
const root = path.resolve(__dirname, "..");
const canonical = value => value && typeof value === "object" && !Array.isArray(value)
  ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
const hash = value => createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");

(async () => {
  const db = new PGlite();
  let checks = 0;
  const check = (actual, expected) => { assert.deepEqual(actual, expected); checks++; };
  await db.exec("CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;");
  let applied = 0;
  for (const name of fs.readdirSync(path.join(root, "supabase/migrations")).filter(name => name.endsWith(".sql")).sort()) {
    // The RAG/vector schema is independent of community persistence and needs a separate extension runtime.
    if (name === "202607190001_ai_rag.sql") continue;
    try { await db.exec(fs.readFileSync(path.join(root, "supabase/migrations", name), "utf8")); applied++; }
    catch (error) { throw new Error(`${name}: ${error.message}`); }
  }
  const query = async (sql, values = []) => (await db.query(sql, values)).rows;
  const rpc = async (name, values) => (await query(`select public.${name}(${values.map((_, i) => "$" + (i + 1)).join(",")}) as result`, values))[0].result;
  const token = "a".repeat(64);
  for (const id of ["student-a", "student-b", "moderator"]) {
    await query("insert into public.exchange_accounts(id,profile,created_at) values($1,$2::jsonb,now()-interval '40 days')",
      [id, JSON.stringify({ email_verified: true, student_status_verified: true, verified_university: id === "student-b" ? "國立臺北大學" : "長庚大學", display_name: "測試學生" })]);
    await query("insert into public.exchange_community_identities(id,account_id,display_name,access_token_hash) values($1,$2,'匿名學生',$3)", ["identity-"+id,id,id === "student-a" ? token : (id === "student-b" ? "b" : "c").repeat(64)]);
  }
  async function publish(type, id, content, mutation = "runtime-mutation-"+id) {
    const server = new Set(["id", "author_id", "author_identity_id", "display_name", "created_at", "updated_at", "revision", "answer_count", "comment_count", "viewer_can_delete", "verified_experience", "deleted", "status"]);
    const semantic = Object.fromEntries(Object.entries(content).filter(([key]) => !server.has(key)));
    const envelope = { operation: "publication", payload: { account_id: "student-a", identity_id: "identity-student-a", access_token_hash: token, resource_type: type, content: semantic } };
    return rpc("exchange_commit_public_community_publication", [mutation, hash(envelope), "student-a", "identity-student-a", token, type, {id,author_id:"identity-student-a",display_name:"匿名學生",...content}]);
  }
  const post = { board_id:"public-study-abroad",board_kind:"public_study_abroad",school_name:"公共留學板",post_type:"discussion",topic:"application",country:null,academic_year:null,application_stage:null,title:"交換申請經驗整理",body:"請記得對照當年度官方申請公告。",identity_mode:"anonymous",status:"approved" };
  check((await publish("post","post-a",post)).status,"committed");
  check((await publish("post","post-b",post)).status,"committed");
  check((await rpc("exchange_set_community_bookmark",["student-a","post-a",true])).status,"committed");
  check((await rpc("exchange_set_community_bookmark",["student-a","post-a",true])).saved,true);
  check((await query("select count(*)::int as count from public.exchange_community_bookmarks where account_id='student-a'"))[0].count,1);
  check((await rpc("exchange_set_community_bookmark",["student-b","post-a",true])).status,"committed");
  const comment = {post_id:"post-a",parent_id:null,deleted:false,identity_mode:"anonymous",body:"這是串內回覆的實際經驗。",status:"approved"};
  const first = await publish("comment","root-a",comment);
  check(first.status,"committed");
  const replay = await publish("comment","fresh-retry-id",comment,"runtime-mutation-root-a");
  check(replay.content,first.content); check(replay.idempotent,true);
  check((await publish("comment","child-a",{...comment,parent_id:"root-a"})).status,"committed");
  check((await publish("comment","cross-post",{...comment,post_id:"post-b",parent_id:"root-a"})).status,"parent_missing");
  check((await publish("comment","grandchild",{...comment,parent_id:"child-a"})).status,"parent_missing");
  check((await query("select parent_id,deleted from public.exchange_community_post_comments where id='child-a'"))[0],{parent_id:"root-a",deleted:false});
  check((await publish("post","university-a",{...post,board_id:"cgu",board_kind:"university_exchange",school_name:"長庚大學"})).status,"committed");
  const react = (who,type,id,reaction) => rpc("exchange_set_community_reaction",[who,type,id,reaction,false]);
  const moderate = (mutation, expected, status) => {
    const payload = {mutation_id:mutation,moderator_id:"moderator",resource_type:"comment",resource_id:"root-a",expected_status:expected,status,note:"核對原文後處理這則留言。"};
    return rpc("exchange_commit_public_community_moderation",[mutation,hash({operation:"moderation",payload}),"moderator","comment","root-a",expected,status,payload.note]);
  };
  check((await react("student-a","post","post-a","helpful")).counts,{helpful:1,thanks:0});
  check((await react("student-a","post","post-a","helpful")).counts,{helpful:1,thanks:0});
  check((await react("student-b","post","post-a","thanks")).counts,{helpful:1,thanks:1});
  check((await react("student-a","post","post-a","thanks")).counts,{helpful:0,thanks:2});
  check((await react("student-a","post","post-a",null)).counts,{helpful:0,thanks:1});
  check((await react("student-a","comment","root-a","helpful")).status,"committed");
  check((await react("student-b","post","university-a","thanks")).status,"forbidden");
  check((await moderate("runtime-hide-root-123","approved","hidden")).status,"committed");
  check((await moderate("runtime-hide-root-123","approved","hidden")).idempotent,true);
  check((await moderate("runtime-conflicting-hide-123","approved","hidden")).status,"status_conflict");
  check((await react("student-a","comment","child-a","thanks")).status,"missing");
  check((await publish("comment","hidden-parent",{...comment,parent_id:"root-a"})).status,"parent_missing");
  check((await moderate("runtime-approve-root-123","hidden","approved")).status,"committed");
  const deletion = { mutation_id:"delete-root-event-123", account_id:"student-a", identity_id:"identity-student-a", access_token_hash:token, resource_type:"comment", resource_id:"root-a" };
  const deleteArgs = [deletion.mutation_id,hash({operation:"delete_public_content",payload:deletion}),deletion.account_id,deletion.identity_id,token,"comment","root-a"];
  check((await rpc("exchange_delete_public_community_content",deleteArgs)).status,"committed");
  check((await rpc("exchange_delete_public_community_content",deleteArgs)).idempotent,true);
  check((await query("select deleted,body,author_identity_id,status from public.exchange_community_post_comments where id='root-a'"))[0],{deleted:true,body:"此留言已刪除",author_identity_id:null,status:"approved"});
  check((await react("student-a","comment","root-a","thanks")).status,"missing");
  check((await react("student-a","comment","child-a","thanks")).status,"committed");
  check((await query("select count(*)::int as count from public.exchange_community_reactions where resource_id='root-a'"))[0].count,0);
  check((await rpc("exchange_commit_community_suspension",["runtime-suspend-event-123","identity-student-a","student-a","moderator",null,new Date(Date.now()+7*86400000).toISOString(),"重複違規，暫停發言。"]) ).status,"committed");
  check((await react("student-a","post","post-a","thanks")).status,"forbidden");
  await db.exec("SET ROLE anon;");
  await assert.rejects(() => query("select * from public.exchange_community_reactions"), /permission denied/); checks++;
  await assert.rejects(() => query("select * from public.exchange_community_bookmarks"), /permission denied/); checks++;
  await assert.rejects(() => rpc("exchange_set_community_bookmark",["student-b","post-a",true]), /permission denied/); checks++;
  await assert.rejects(() => react("student-b","post","post-a","helpful"), /permission denied/); checks++;
  await db.exec("RESET ROLE; SET ROLE authenticated;");
  await assert.rejects(() => react("student-b","post","post-a","helpful"), /permission denied/); checks++;
  await db.exec("RESET ROLE;");
  check((await query("select count(*)::int as count from public.exchange_community_moderation_audits where resource_id='root-a'"))[0].count,2);
  await query("delete from public.exchange_accounts where id='student-b'");
  check((await query("select count(*)::int as count from public.exchange_community_reactions where account_id='student-b'"))[0].count,0);
  check((await query("select count(*)::int as count from public.exchange_community_bookmarks where account_id='student-b'"))[0].count,0);
  await query("delete from public.exchange_community_posts where id='post-a'");
  check((await query("select count(*)::int as count from public.exchange_community_reactions"))[0].count,0);
  check((await query("select count(*)::int as count from public.exchange_community_bookmarks"))[0].count,0);
  await db.close();
  console.log(JSON.stringify({runtime:"PGlite PostgreSQL",applied_migrations:applied,checks,network_database_access:false}));
})().catch(error => { console.error(error.stack); process.exit(1); });
