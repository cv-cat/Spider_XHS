class User_Detail():
    def __init__(self, id, userId, nickname, avatar, desc, follows, fans, interaction, ipLocation, gender, tags):
        self.id = id
        self.userId = userId
        self.nickname = nickname
        self.avatar = avatar
        self.desc = desc
        self.follows = follows
        self.fans = fans
        self.interaction = interaction
        self.ipLocation = ipLocation
        self.gender = gender
        self.tags = tags


    def __str__(self):
        # 每个值都要换行
        return f'id: {self.id}\n' \
                f'userId: {self.userId}\n' \
                f'nickname: {self.nickname}\n' \
                f'avatar: {self.avatar}\n' \
                f'desc: {self.desc}\n' \
                f'follows: {self.follows}\n' \
                f'fans: {self.fans}\n' \
                f'interaction: {self.interaction}\n' \
                f'ipLocation: {self.ipLocation}\n' \
                f'gender: {self.gender}\n' \
                f'tags: {self.tags}\n' \



