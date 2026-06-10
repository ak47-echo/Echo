def get_policy():

    policy = []

    try:

        with open("../03_Knowledge/echo_policy.txt", "r") as file:

            for line in file:
                policy.append(line.strip())

    except:

        policy.append("Policy file unavailable.")

    return policy