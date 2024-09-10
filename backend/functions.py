from statistics import mean
from config import config
from datetime import timezone


def set_new_ratings(users, result):
    avg_prediction = round(mean([u.prediction for u in users]), 4)
    total_loss = 0

    # Set point gain/loss
    for user in users:
        have_yes_shares = 1 if user.prediction >= avg_prediction else 0
        middle_spread = mean([user.prediction, avg_prediction])
        price = middle_spread if have_yes_shares else 1 - middle_spread
        user.points = 1 - price if result == have_yes_shares else -price

        total_loss += abs(middle_spread - avg_prediction)

    avg_loss = total_loss / len(users)

    # Apply Elo
    for user in users:
        opponent_rating = mean([u.rating for u in users if u.id != user.id])
        win_chance = 1 / (1 + pow(10, (opponent_rating - user.rating) / 400.0))
        win = 1 if user.points >= 0 else 0
        user.new_rating = user.rating + abs(user.points + avg_loss) * user.kfactor * (win - win_chance)

    # Update ratings & kfactor
    for user in users:
        if user.kfactor > config["kfactor_min"]:
            user.kfactor -= config["kfactor_change"]
            if user.kfactor < config["kfactor_min"]:
                user.kfactor = config["kfactor_min"]

        old_rating = user.rating

        user.rating_gained = user.new_rating - user.rating
        user.rating = user.new_rating

        # Public rating
        if old_rating == user.public_rating:
            # If they are already equal, keep it that way
            user.public_rating = user.new_rating
            user.public_rating_gained = user.rating_gained
            continue

        current_public_rating = user.public_rating

        if current_public_rating > user.rating:
            # If our real rating went down such that it's now lower than our public rating, equalize them
            user.public_rating = user.rating
            user.public_rating_gained = user.public_rating - current_public_rating
        else:
            multiplier = (user.rating - user.public_rating) / 2
            if multiplier < 1:
                multiplier = 1

            if user.rating_gained > 0:
                user.public_rating_gained = user.rating_gained * (1.5 * multiplier)
            else:
                user.public_rating_gained = user.rating_gained * (0.5 / multiplier)

            user.public_rating += user.public_rating_gained

            if user.public_rating > user.rating:
                # If our public rating overtook our real rating, equalize them
                user.public_rating = user.rating
                user.public_rating_gained = user.public_rating - current_public_rating


def remove_timezone(dt):
    return dt.replace(tzinfo=None)


def as_utc(dt):
    return dt.replace(tzinfo=timezone.utc)
