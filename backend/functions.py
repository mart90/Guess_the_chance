from statistics import mean


def set_new_ratings(users, result):
    avg_prediction = round(mean([u.prediction for u in users]), 4)

    for user in users:
        opponent_rating = mean([u.rating for u in users if u.id != user.id])
        have_yes_shares = 1 if user.prediction >= avg_prediction else 0
        middle_spread = mean([user.prediction, avg_prediction])
        price = middle_spread if have_yes_shares else 1 - middle_spread
        points = 1 - price if result == have_yes_shares else -price
        win = 1 if points >= 0 else 0

        win_chance = 1 / (1 + pow(10, (opponent_rating - user.rating) / 400.0))

        user.new_rating = user.rating + points * user.kfactor * abs(win - win_chance)
        if user.kfactor > 0.2:
            user.kfactor -= 0.001
            if user.kfactor < 0.2:
                user.kfactor = 0.2

    #zero_sum_compensation = mean([u.new_rating - u.rating for u in users])

    for user in users:
        #user.new_rating -= zero_sum_compensation
        user.rating_gained = user.new_rating - user.rating
        user.rating = user.new_rating
