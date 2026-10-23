"""Evergreen topics for the offline writer, used when no Claude credentials are configured.

Every point is general advice that holds across schools; anything school-specific says to check the official notice.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    key: str
    title: str  # carousel cover / video hook
    hook: str  # first line on Threads
    points: tuple[tuple[str, str], ...]  # (heading ≤ 12 chars, one-line detail)
    question: str
    choice: tuple[str, str, str]  # (question, option A, option B)
    story: str  # 小編碎碎念
    feature: str  # the UniWay feature that helps


TOPICS: tuple[Topic, ...] = (
    Topic(
        key="study-plan",
        title="讀書計畫寫不出來？先回答這 3 題",
        hook="讀書計畫打開空白文件 30 分鐘還是 0 字的人舉手 🙋",
        points=(
            ("為什麼是這間", "寫出課程、研究或環境的具體理由，不要只寫排名"),
            ("想修哪些課", "列 2～3 門課，說明和你科系的關聯"),
            ("回來之後", "交換經驗怎麼接回你的畢業或職涯計畫"),
            ("字數照規定", "各校字數與格式不同，送件前再對一次"),
        ),
        question="你卡在哪一段？留言告訴小編，下一篇幫你拆解",
        choice=("讀書計畫你會先寫？", "A 先寫中文草稿再翻", "B 直接用英文寫"),
        story="今天整理讀書計畫的字數規定，發現同一間學校不同年度都可能改。所以每次都要回去看當年度簡章，真的不能偷懶 😮‍💨",
        feature="UniWay 申請工作台幫你整理各校讀書計畫字數與送件規定",
    ),
    Topic(
        key="language-test",
        title="托福、雅思、多益，交換該考哪個？",
        hook="還沒決定要考托福還雅思的交換生，先看這篇再報名",
        points=(
            ("先看目標學校", "每間合作校接受的檢定與分數都不一樣"),
            ("注意有效期限", "成績多半有期限，以各校規定為準"),
            ("預留重考時間", "從報名到拿成績要好幾週，提早排"),
            ("確認考試版本", "有些學校不收居家版，報名前先查"),
        ),
        question="你目前考了哪一種？分數卡在哪一段？",
        choice=("語言檢定你會選？", "A 托福", "B 雅思"),
        story="小編今天又看到一間合作校更新語言門檻，新舊制分數並列。這種細節真的很容易漏看，所以我們每筆都附官方來源讓你自己點進去確認。",
        feature="UniWay 依語言檢定與分數篩選你能申請的合作校",
    ),
    Topic(
        key="budget",
        title="交換一學期要準備多少錢？",
        hook="交換前最常被問：一學期到底要存多少錢？",
        points=(
            ("機票", "提早訂通常比較划算，開學前後最貴"),
            ("住宿", "宿舍和校外租屋差很多，先看學校資訊"),
            ("生活費", "參考官方公布的生活費，而不是網路印象"),
            ("保險簽證", "簽證費、保險與押金常被忘記算進去"),
        ),
        question="你最擔心哪一筆開銷？",
        choice=("交換預算你會？", "A 先存好全額再出發", "B 邊打工邊補"),
        story="做預算功能的時候，最頭痛的是每間學校公布生活費的幣別和期間都不一樣。最後決定全部換成同一個幣別估算，比較好比較。",
        feature="UniWay 交換預算用同一幣別估算總成本，附官方生活費來源",
    ),
    Topic(
        key="choose-school",
        title="選交換學校，別只看排名",
        hook="選交換學校只看 QS 排名的人，可能會錯過最適合你的那間",
        points=(
            ("名額與門檻", "先刪掉資格不符的，省下很多時間"),
            ("開放學期", "有些學校只收上或下學期"),
            ("課程能不能修", "確認想修的課有開放給交換生"),
            ("生活成本", "同一個國家不同城市也差很多"),
        ),
        question="你選校最在意的是什麼？",
        choice=("選交換學校你會先看？", "A 學校名氣", "B 城市生活"),
        story="小編當年選校只看排名，結果到了才發現想修的課不開放給交換生 🥲 所以現在做 UniWay 一定把這些條件放進篩選。",
        feature="UniWay 依國家、學期、語言檢定、名額一鍵篩選合作校",
    ),
    Topic(
        key="deadlines",
        title="校內截止日，比你想的早很多",
        hook="以為交換申請還很久？校內甄選截止日通常比國外學校早很多",
        points=(
            ("先抓校內截止", "母校甄選才是第一關，日期以公告為準"),
            ("往回推時間", "語檢、成績單、推薦信都需要等"),
            ("排出提醒", "截止前兩週開始倒數，最後一週不要只剩讀書計畫"),
            ("確認送件方式", "線上、紙本或寄信，規定都不同"),
        ),
        question="你的學校甄選截止日你記下來了嗎？",
        choice=("你是哪一型？", "A 提前一個月準備", "B 截止前一週衝刺"),
        story="整理各校時程時發現，同一學年不同學校的甄選可能差好幾個月。真的很建議把日期丟進行事曆，不要只靠記憶。",
        feature="UniWay 一鍵把校內截止日加進 Google／Apple 行事曆，倒數提醒",
    ),
    Topic(
        key="recommendation",
        title="推薦信，要多早找老師？",
        hook="推薦信不要截止前三天才找老師（真心建議）",
        points=(
            ("提早詢問", "至少提早三到四週，給老師時間"),
            ("附上資料", "成績單、讀書計畫草稿、目標學校"),
            ("確認繳交方式", "紙本彌封、線上上傳還是老師直接寄"),
            ("提醒與感謝", "截止前一週禮貌提醒，結束後記得道謝"),
        ),
        question="你會找哪一類老師寫推薦信？",
        choice=("推薦信你會找？", "A 修過課的老師", "B 專題指導老師"),
        story="收到不少同學問推薦信要怎麼開口。其實老師最怕的是資料不齊又很趕，先把資料準備好，開口就容易多了。",
        feature="UniWay 申請文件清單幫你逐項確認要準備的文件",
    ),
    Topic(
        key="scholarship",
        title="交換補助，別等錄取才查",
        hook="很多交換補助的申請時間，跟交換甄選差不多同時",
        points=(
            ("母校補助", "先看國際處公告，有些和甄選一起申請"),
            ("政府補助", "例如教育部的學海系列，時程以公告為準"),
            ("合作校獎學金", "部分合作校有交換生專屬方案"),
            ("文件一起準備", "讀書計畫與成績單常可共用，省時間"),
        ),
        question="你有查過自己學校的交換補助嗎？",
        choice=("交換補助你會？", "A 全部都申請看看", "B 只挑最有機會的"),
        story="小編整理補助資料時最常看到一句話：「逾期不受理」。補助通常不會為你延期，所以真的要早點查。",
        feature="UniWay 預算與補助頁整理各校交換補助與官方來源",
    ),
    Topic(
        key="credits",
        title="交換回來，學分抵得了嗎？",
        hook="交換回來才發現學分抵不了，是最痛的那種 😭",
        points=(
            ("出發前先問", "找系辦確認抵免規則與流程"),
            ("留好課程大綱", "抵免常需要 syllabus，先存起來"),
            ("選課留備案", "到當地常有課額滿，多準備幾門"),
            ("成績單時程", "有些學校成績單較晚核發，影響畢業規劃"),
        ),
        question="你們系上交換學分好抵嗎？",
        choice=("交換你會？", "A 以抵免學分為主", "B 修自己有興趣的課"),
        story="最近整理到有學校提醒：交換成績單通常在下一學期開學後才核發。小編看到這句心裡一驚，這對大四同學影響超大。",
        feature="UniWay 學長姐心得整理選課、抵免與生活經驗",
    ),
)


def topic_for(seed: int) -> Topic:
    return TOPICS[seed % len(TOPICS)]
