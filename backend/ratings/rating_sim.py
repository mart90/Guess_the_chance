import numpy
import matplotlib.pyplot as plt
from random import randint
from functions import set_new_ratings


class User(object):
    def __init__(self, id):
        self.id = id
        self.rating = 0
        self.new_rating = 0
        self.kfactor = 1
        self.rating_history = [0]
        self.prediction = None

    def make_prediction(self, rng, p):
        if self.id == "PoC":
            self.prediction = p
        elif self.id == "Off by 0.1":
            self.prediction = p - 0.1 if randint(0,1) == 0 else p + 0.1
        elif self.id == "Perfect std dev":
            self.prediction = rng.normal(p, 0.1)
        elif self.id == "Always right direction":
            self.prediction = 1 if p >= 0.5 else 0
        elif self.id.startswith("Random"):
            self.prediction = randint(0, 100) / 100

        if self.prediction < 0:
            self.prediction = 0
        elif self.prediction > 1:
            self.prediction = 1


tries = 10000

users = [
    User("PoC"),
    User("Off by 0.1"),
    User("Perfect std dev"),
    User("Always right direction"),
    User("Random"),
    # User("Random2"),
    # User("Random3")
]

results = []
rng = numpy.random.default_rng()

for i in range(tries):
    if i == tries - 2:
        pass

    real_probability = randint(20, 80) / 100

    for user in users:
        user.make_prediction(rng, real_probability)

    avg_prediction = numpy.mean([user.prediction for user in users])

    r = randint(1, 100)
    if r <= real_probability * 100:
        result = 1
    else:
        result = 0
    results.append(result)

    set_new_ratings(users, result)

    for user in users:
        user.rating = user.new_rating
        user.rating_history.append(user.rating)

for user in users:
    plt.plot(user.rating_history, label=user.id)
    print("%s last rating: %s" % (user.id, user.rating))

for user in users:
    avg_rating = numpy.mean(user.rating_history)
    #plt.plot([avg_rating for i in range(tries)], label="%s average %s" % (user.name, round(avg_rating)))

average_result = numpy.mean(results)
print(average_result)

plt.legend()
plt.show()
