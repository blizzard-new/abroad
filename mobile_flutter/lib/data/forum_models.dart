import 'models.dart';

const forumTopics = {
  'application': '申請',
  'housing': '住宿',
  'academics': '課程',
  'life': '生活',
  'pre_departure': '行前準備',
  'scholarship': '獎學金',
  'visa': '簽證',
  'cost': '生活費',
  'career': '職涯',
  'warning': '經驗提醒',
};

class ForumBoard {
  ForumBoard.fromJson(dynamic data) {
    final row = jsonMap(data);
    id = textValue(row['id']);
    label = textValue(row['label']);
    canRead = row['can_read'] == true;
    canPost = row['can_post'] == true;
    canComment = row['can_comment'] == true;
    reason = textValue(row['unavailable_reason']);
  }
  late final String id, label, reason;
  late final bool canRead, canPost, canComment;
}

class ForumPost {
  ForumPost.fromJson(dynamic data) {
    final row = jsonMap(data);
    id = textValue(row['id']);
    boardId = textValue(row['board_id']);
    school = textValue(row['school_name']);
    title = textValue(row['title']);
    body = textValue(row['body'], textValue(row['excerpt']));
    author = textValue(row['display_name'], '匿名同學');
    topic = textValue(row['topic']);
    created = textValue(row['created_at']);
    comments = row['comment_count'] as int? ?? 0;
    canDelete = row['viewer_can_delete'] == true;
  }
  late final String id, boardId, school, title, body, author, topic, created;
  late final int comments;
  late final bool canDelete;
}

class ForumReply {
  ForumReply.fromJson(dynamic data) {
    final row = jsonMap(data);
    id = textValue(row['id']);
    body = row['deleted'] == true ? '這則回覆已刪除' : textValue(row['body']);
    author = textValue(row['display_name'], '匿名同學');
    created = textValue(row['created_at']);
    replyCount = row['reply_count'] as int? ?? 0;
    canDelete = row['viewer_can_delete'] == true;
  }
  late final String id, body, author, created;
  late final int replyCount;
  late final bool canDelete;
}

class ForumPage<T> {
  const ForumPage(this.items, this.next);
  final List<T> items;
  final String? next;
}
