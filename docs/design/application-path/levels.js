/* Existing workflow references + smaller UX actions. These are not new school requirements. */
window.UniWayPreviewLevels = function buildLevels(source) {
  const rule = source.steps;
  const level = (id, title, icon, kind, prompt, group, extra = {}) => ({id,title,icon,kind,prompt,rule:rule[group],...extra});
  const writing = (id,title,prompt,example) => level(id,title,'notebook-pen','write',prompt,1,{example,writing:true});
  const file = (id,title,filename,group = 1) => level(id,title,'file-up','file','先放好這一份文件，再確認內容清楚、版本適用。',group,{filename});
  const note = (id,title,icon,prompt,group) => level(id,title,icon,'note',prompt,group);
  return [
    {title:'找到你的方向',icon:'compass',hint:'先選母校、學期和目標',levels:[
      level('home','確認你的母校','school','home','以母校的交換規定安排這趟旅程。',0),
      level('term','選擇出國學期','calendar-days','term','先記下預計出發的學期；還沒決定也可以。',0),
      level('target','確認交換目標','map-pin','target','這份計畫只記錄這一所交換學校的準備。',0),
    ]},
    {title:'釐清申請條件',icon:'badge-check',hint:'一次確認一項關鍵條件',levels:[
      level('eligibility','核對申請資格','badge-check','checks','先確認適用的年度、學制與院系。',0,{checks:['我已查看適用年度與學制','我已核對自己的院系條件']}),
      level('language-track','記下申請語組','languages','language','依母校與交換校規定，記下想申請的語組。',0),
      note('deadline','確認申請時程','calendar-search','目前沒有可採用的確切日期。先記下要向誰確認。',0),
    ]},
    {title:'寫出交換的理由',icon:'pencil-line',hint:'每關只寫一小段',levels:[
      writing('motivation','寫一段申請動機','你想透過交換，補足哪一項學習上的不足？','我在＿＿課程遇到＿＿問題，希望透過交換學習＿＿，回來後用在＿＿。'),
      writing('school-reason','寫下選校原因','這間學校的什麼課程或資源，剛好適合你？','我關注＿＿領域，想運用該校的＿＿課程／資源，進一步完成＿＿。請以實際查到的資訊填寫。'),
      writing('learning-goals','設定研修目標','交換結束時，你希望自己做得到什麼？','我希望能＿＿。我會用＿＿成果，檢查自己是否達成。'),
    ]},
    {title:'規劃交換的收穫',icon:'book-open',hint:'從一門課、一個成果開始',levels:[
      level('course-plan','記下一門想修的課','book-open','course','先找到一門感興趣的課，再記下想學什麼。',1,{writing:true}),
      writing('expected-outcomes','描繪預期成果','你想帶回什麼具體成果？','完成＿＿課程／作品，並整理成＿＿，用來分享或延伸研究。'),
      writing('return-plan','連結返國後的學習','回到母校後，這段經驗會如何繼續？','我會將＿＿運用在＿＿，並向＿＿分享這次學到的內容。'),
    ]},
    {title:'整理研修計畫',icon:'notebook-tabs',hint:'把剛剛的小段落接起來',levels:[
      level('assemble','預覽你的研修計畫','notebook-tabs','assemble','把前六段集中看一次，不必重新貼上。',1),
      level('format','核對篇幅與語言','spell-check','checks','寫作分段是輔助工具；正式格式依母校當期規定。',1,{checks:['已核對當期篇幅與格式','已核對語組要求的撰寫語言'],warning:'舊畫面同時出現字數與頁數上限；本預覽不代替你判定哪一版適用。'}),
    ]},
    {title:'備齊成績與語言證明',icon:'files',hint:'一關只整理一份文件',levels:[
      file('transcript','準備正式成績單','正式成績單-示意.pdf'),
      file('rank','準備排名資料','排名資料-示意.pdf'),
      file('language-file','準備語言證明','語言證明-示意.pdf'),
    ]},
    {title:'整理申請表',icon:'file-signature',hint:'確認資料，再放好簽名版本',levels:[
      note('form-details','核對申請表資料','contact-round','查看申請表，記下還需要確認或補上的一項資料。',1),
      file('signed-form','放好簽名申請表','簽名申請表-示意.pdf'),
    ]},
    {title:'完成校內送件',icon:'send',hint:'最後檢查，再到官方系統提交',levels:[
      level('preferences','確認志願順序','list-ordered','preferences','這份計畫的目標學校，預計排在第幾志願？',0),
      level('packet','檢查送件資料','folder-check','packet','集中看文件準備狀態，再做最後確認。',1),
      level('submission','記錄校內送件','send','submission','到校方系統完成後，再回來記下送件情況。',1),
    ]},
    {title:'追蹤校方通知',icon:'mail','hint':'有新通知時，再回來更新',levels:[
      level('review','記錄校內審查通知','messages-square','notice','把面試或補件通知記在這裡。沒有通知就保持未記錄。',2,{external:true}),
      level('nomination','記錄提名通知','mail-check','notice','有收到提名信，再記錄下一步與通知來源。',3,{external:true}),
    ]},
    {title:'完成交換校申請',icon:'globe-2',hint:'依收到的提名信逐項辦理',levels:[
      level('host-requirements','確認交換校清單','list-checks','checks','以提名信和交換校當期規定核對，不直接沿用母校文件。',3,{checks:['已查看提名信的申請步驟','已核對交換校文件清單']}),
      file('host-files','整理交換校文件','交換校文件-示意.pdf',3),
      level('host-submission','記錄交換校送件','send','submission','完成交換校系統送件後，記下自己的送件紀錄。',3),
    ]},
    {title:'把出發準備好',icon:'luggage',hint:'錄取後，一次安排一件事',levels:[
      note('visa','確認簽證辦理方式','badge','先確認適用簽證與辦理窗口，記下下一個動作。',4),
      note('housing','安排住宿','house','記下目前住宿安排，以及還需要確認的事項。',4),
      note('insurance','確認保險要求','shield-check','依學校與目的地要求，記下要準備的保險。',4),
      note('preflight-courses','確認行前選課','notebook','依錄取與母校規定，記下行前選課要完成的下一步。',4),
    ]},
    {title:'完成交換的最後一哩',icon:'flag',hint:'從抵達到返國，留下完整紀錄',levels:[
      note('arrival','記下抵達回報','map-pinned','依母校規定，記錄抵達回報的辦理情況。',5),
      level('reflection','整理交換心得','notebook-pen','write','先記下一段最想分享的交換經驗。',5,{example:'我在＿＿學到＿＿，這讓我重新理解＿＿。'}),
      note('credit','確認學分採認','graduation-cap','記下返國後要交給系所或註冊組的資料。',5),
    ]},
  ].map((stage,index)=>({...stage,index,levels:stage.levels.map(l=>({...l,stage:index}))}));
};
