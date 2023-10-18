class Note_Detail(): 
    def __init__(self, id, note_id, note_type, user_id, nickname, avatar, title, desc, liked_count, collected_count, comment_count, share_count, video_addr, image_list, tag_list, upload_time, ip_location):
        self.id = id
        self.note_id = note_id
        self.note_type = note_type
        self.user_id = user_id
        self.nickname = nickname
        self.avatar = avatar
        self.title = title
        self.desc = desc
        self.liked_count = liked_count
        self.collected_count = collected_count
        self.comment_count = comment_count
        self.share_count = share_count
        self.video_addr = video_addr
        self.image_list = image_list
        self.tag_list = tag_list
        self.upload_time = upload_time
        self.ip_location = ip_location

    def __str__(self):
        # 每个值都要换行
        return f'id: {self.id}\n' \
                f'note_id: {self.note_id}\n' \
                f'user_id: {self.user_id}\n' \
                f'nickname: {self.nickname}\n' \
                f'avatar: {self.avatar}\n' \
                f'title: {self.title}\n' \
                f'desc: {self.desc}\n' \
                f'liked_count: {self.liked_count}\n' \
                f'collected_count: {self.collected_count}\n' \
                f'comment_count: {self.comment_count}\n' \
                f'share_count: {self.share_count}\n' \
                f'video_addr: {self.video_addr}\n' \
                f'images: {self.image_list}\n' \
                f'tag_list: {self.tag_list}\n' \
                f'upload_time: {self.upload_time}\n' \
                f'note_ip_location: {self.ip_location}\n'


