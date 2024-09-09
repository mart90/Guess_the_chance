class User:
    def __init__(self, id, username, rating, kfactor, is_admin):
        self.id = id
        self.username = username
        self.hashedPassword = None
        self.rating = rating
        self.kfactor = kfactor
        self.is_admin = True if is_admin == 1 else False

        self.prediction = None
        self.points = None
        self.new_rating = None
        self.rating_gained = None
        self.public_rating = None
        self.public_rating_gained = None

    def insert(self, mysql):
        values = (
            self.username,
            self.hashedPassword
        )
        mysql.query("INSERT INTO user (username, password_hash) VALUES (%s, %s)", values)

    def update_rating(self, mysql, event_id):
        values = (
            self.rating,
            self.public_rating,
            self.kfactor,
            self.id
        )
        mysql.query("update user set rating = %s, public_rating = %s, kfactor = %s where id = %s", values)

        values = (
            self.rating,
            self.rating_gained,
            self.public_rating,
            self.public_rating_gained,
            self.id,
            event_id
        )
        mysql.query("""
            UPDATE prediction 
            SET 
                new_rating = %s, 
                rating_gained = %s,
                new_public_rating = %s,
                public_rating_gained = %s
            WHERE 
                user_id = %s 
                AND event_id = %s""", values)
