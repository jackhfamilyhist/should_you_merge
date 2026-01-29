prepanswers = []
givenanswers = []
skip = False

#additional AI coded function to help from lines 6 to 126, because an approximate is much better than no approximate, especially when (in this case) it has been tested and yields plausible results
import math
from functools import lru_cache
RADIX = 100_000
MAX_AGE = 110  # start of open interval (110+)
BASE_SILER = (0.175, 1.40, 0.00368, 0.000075, 0.0917)
def siler_mu(age: float, a1, b1, a2, a3, b3) -> float:
    return a1 * math.exp(-b1 * age) + a2 + a3 * math.exp(b3 * age)

def accident_hump_mu(age: float, amp: float, center: float = 23.0, sigma: float = 7.0) -> float:
    z = (age - center) / sigma
    return amp * math.exp(-0.5 * z * z)

def mu_total(age: float, k: float, hump_amp: float, siler_params=BASE_SILER) -> float:
    a1, b1, a2, a3, b3 = siler_params
    return k * siler_mu(age, a1, b1, a2, a3, b3) + accident_hump_mu(age, hump_amp)

def life_table_from_mu(k: float, hump_amp: float):
    """
    Returns:
      e0: life expectancy at birth
      lx: survivors at each exact age 0..MAX_AGE
      dx: deaths in each interval:
          0..MAX_AGE-1 are 1-year intervals, and dx[MAX_AGE] is the open interval (MAX_AGE+)
    """
    lx = [RADIX]
    dx = []
    Lx = []
    # Ages 0..MAX_AGE-1 as 1-year intervals
    for age in range(MAX_AGE):
        mu = mu_total(age, k=k, hump_amp=hump_amp)
        qx = 1.0 - math.exp(-mu)          # 1-year interval approximation
        qx = min(max(qx, 0.0), 1.0)

        d = lx[age] * qx
        dx.append(d)

        lx_next = lx[age] - d
        lx.append(lx_next)

        # UDD person-years in interval
        Lx.append(lx[age] - 0.5 * d)
    # Open interval at age MAX_AGE+
    l_open = lx[MAX_AGE]
    mu_open = max(mu_total(MAX_AGE, k=k, hump_amp=hump_amp), 1e-12)
    dx.append(l_open)                 # everyone remaining eventually dies in open interval
    Lx.append(l_open / mu_open)       # constant-hazard approximation for open interval person-years
    e0 = sum(Lx) / RADIX
    return e0, lx, dx

def solve_k_for_target_e0(target_e0: float, hump_amp: float):
    lo, hi = 1e-4, 150.0
    for _ in range(95):
        mid = (lo + hi) / 2.0
        e0_mid, _, _ = life_table_from_mu(mid, hump_amp=hump_amp)
        if e0_mid > target_e0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0

def target_e0(birthyear: int, scenario: str) -> float:
    scenario = scenario.lower()
    if scenario not in {"low", "mid", "high"}:
        raise ValueError("scenario must be 'low', 'mid', or 'high'")

    if scenario == "low":
        e1600, e1800, e1900, e1950, e1999 = 27.0, 32.0, 28.0, 40.0, 60.0
        dip_amp = 2.5
    elif scenario == "mid":
        e1600, e1800, e1900, e1950, e1999 = 32.0, 38.0, 32.0, 48.0, 74.0
        dip_amp = 2.0
    else:  # high
        e1600, e1800, e1900, e1950, e1999 = 36.0, 40.0, 45.0, 60.0, 80.0
        dip_amp = 1.5
    def lerp(y0, y1, t): 
        return y0 + (y1 - y0) * t
    if birthyear <= 1800:
        t = (birthyear - 1600) / 200.0
        t = min(max(t, 0.0), 1.0)
        e = lerp(e1600, e1800, t)

        dip = dip_amp * math.exp(-0.5 * ((birthyear - 1700) / 45.0) ** 2)
        e = e - dip
        e = min(e, 40.0)
        return max(20.0, e)
    if birthyear <= 1900:
        t = (birthyear - 1800) / 100.0
        return lerp(e1800, e1900, t)
    if birthyear <= 1950:
        t = (birthyear - 1900) / 50.0
        return lerp(e1900, e1950, t)
    if birthyear <= 1999:
        t = (birthyear - 1950) / 49.0
        return lerp(e1950, e1999, t)
    return e1999

def hump_amp_for_scenario(scenario: str) -> float:
    s = scenario.lower()
    return {"low": 0.0012, "mid": 0.0008, "high": 0.0005}[s]

@lru_cache(maxsize=5000)
def cohort_probs_for_birthyear(birthyear: int, scenario: str):
    scenario = scenario.lower()
    e0 = target_e0(birthyear, scenario)
    hump_amp = hump_amp_for_scenario(scenario)
    k = solve_k_for_target_e0(e0, hump_amp=hump_amp)
    _, _, dx = life_table_from_mu(k, hump_amp=hump_amp)
    # dx has length MAX_AGE+1 (including open interval)
    probs = [d / RADIX for d in dx]
    # probs should sum to ~1.0 now
    return probs

def f(birthyear: int, deathyear: int, scenario: str = "mid") -> float:
    age = deathyear - birthyear
    if age < 0:
        return 0.0
    probs = cohort_probs_for_birthyear(birthyear, scenario)
    # If they "die at age >= MAX_AGE", put it into the open interval bucket.
    if age >= MAX_AGE:
        return probs[MAX_AGE]
    return probs[int(age)]

def printif(text1):
    global prepanswers, skip
    if not skip:
        if not prepanswers:
            print(linefit(text1))

def linefit(string1):
    helper99 = 0
    while string1[helper99] == '\n':
        helper99 += 1
    helper100 = string1.split()
    helper101 = ''
    while helper99:
        helper99 -= 1
        helper101 = helper101 + '\n'
    while helper100:
        helper102 = ''
        maxlinelen = 79
        if '\t' in string1:
            helper102 = '\t'
            maxlinelen = 72
        while helper100 and (len(helper102) + len(helper100[0]) <= maxlinelen):
            helper102 = helper102 + helper100[0]
            del helper100[0]
            if len(helper102) < maxlinelen:
                helper102 = helper102 + ' '
        if helper100:
            helper102 = helper102 + '\n'
        helper101 = helper101 + helper102
    return helper101

def inpfor(prompt, answers):
    global prepanswers, givenanswers, skip
    altanswerdict = {}
    wordsforyes = ['yes', 'so', 'sure', 'same', 'indeed', 'totally', 'surely', 'completely', 'aff', 'water is wet', 'they match', '1', 'one', 'yea', 'both', 'do', 'obvi']
    for word1 in wordsforyes:
        altanswerdict[word1] = 'y'
    wordsforno = ['no', 'not', 'na', 'dif', 'nu', 'opposite', 'incompletely', 'neg', "n't", '0', 'zero', 'never', 'dis', ' fly', 'mis']
    for word1 in wordsforno:
        altanswerdict[word1] = 'n'
    wordsforunsure = ['unsure', 'may', 'probably', 'possibly', 'potentially', '?', 'seeking', 'undetermined', "don't", 'do not', 'skip', 'could', 'either', 'next', ' if', 'if ', 'know']
    for word1 in wordsforunsure:
        altanswerdict[word1] = 'u' if len(answers) > 2 else ('n' if 'n' in answers else answers[0])
    wordsforpartial = ['part', 'piece', 'side', 'conta']
    for word1 in wordsforpartial:
        altanswerdict[word1] = 'p'
    wordsforundo = ['undo', 'back', 'previous', 'ret', 'prior']
    for word1 in wordsforundo:
        altanswerdict[word1] = 'undo'
    wordsforfather = ['father', 'male', 'dad']
    for word1 in wordsforfather:
        altanswerdict[word1] = 'father'
    wordsformother = ['mother', 'fema', 'mom']
    for word1 in wordsformother:
        altanswerdict[word1] = 'mother'
    wordsforparent = ['parent']
    if 'parent' in givenanswers:
        wordsforparent = wordsforparent + wordsforunsure
    for word1 in wordsforparent:
        altanswerdict[word1] = 'parent'
    if len(answers) == 1:
        return answers[0]
    if not skip:
        choice = "include this string in possible answers only if you want your code to fail"
        helper2 = '\n\n' + prompt
        helper2 = helper2 + "  "
        for answer in answers:
            answer = answer.lower()
            helper2 = helper2 + answer
            if answer != answers[-1]:
                helper2 = helper2 + "/"
            else:
                helper2 = helper2 + ":  "
        while not choice in (answers + ['undo']):
            if prepanswers:
                choice = prepanswers[0]
                del prepanswers[0]
            else:
                choice = input(linefit(helper2)).lower()
                if not choice in (answers + ['undo']):
                    choice2 = choice
                    for hint in list(altanswerdict.keys()):
                        if hint in choice:
                            choice2 = altanswerdict[hint]
                    choice = choice2
                    if choice == 'y':
                        printif('ANSWER TAKEN AFFIRMATIVELY')
                    elif choice == 'n':
                        printif('ANSWER TAKEN AS NEGATION')
                    elif choice == 'p':
                        printif('ANSWER TAKEN AS PARTIAL INFORMATION MATCH')
                    elif choice == 'u':
                        printif('ANSWER TAKEN AS LACK OF DATA, MOVING ON')
                    elif choice == 'father':
                        printif('ANSWER TAKEN AS REFERRING TO RELATIONSHIP BETWEEN A FATHER AND CHILD')
                    elif choice == 'mother':
                        printif('ANSWER TAKEN AS REFERRING TO RELATIONSHIP BETWEEN A MOTHER AND CHILD')
                    elif choice == 'parent':
                        printif('ANSWER TAKEN AS REFERRING TO RELATIONSHIP BETWEEN A PARENTAL FIGURE OF UNKNOWN SEX/GENDER AND THEIR CHILD')
                if not choice in (answers + ['undo']):
                    printif("invalid response, try again.")
        if choice != 'undo':
            givenanswers.append(choice)
        else:
            prepanswers = givenanswers[:-1]
            if len(givenanswers) > 7 and givenanswers[-3:] == ['u', 'u', 'u'] and givenanswers[-7] in ['father', 'mother', 'parent']:
                prepanswers = givenanswers[:-4]
            skip = True
            choice = answers[0].lower()
            if not prepanswers:
                prepanswers.append(0)
    else:
        choice = answers[0].lower()
    return choice

def inpforany(prompt):
    global prepanswers, givenanswers, skip
    if not skip:
        choice = "include this string in possible answers only if you want your code to fail"
        helper2 = '\n\n' + prompt
        helper2 = helper2 + "  "
        if prepanswers:
            choice = prepanswers[0]
            del prepanswers[0]
        else:
            choice = input(linefit(helper2)).lower()
        if choice != 'undo':
            givenanswers.append(choice)
        else:
            prepanswers = givenanswers[:-1]
            skip = True
            choice = 'hello'
            if not prepanswers:
                prepanswers.append(0)
    else:
        choice = 'hello'
    return choice

def inpnum(prompt, min1, max1):
    global prepanswers, givenanswers, skip
    helper = skip
    while not helper:
        if not prepanswers:
            helper = input(linefit(f"{'\n\n' + prompt}  number answer, no commas:  "))
            for hint in ['undo', 'back', 'previous', 'ret', 'prior']:
                if hint in helper:
                    helper = 'undo'
            if not helper.lower() == 'undo':
                helper2 = helper
                assemblehelper = ''
                helper = [char for char in helper]
                for char in helper:
                    if char in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']:
                        assemblehelper = assemblehelper + char
                helper = assemblehelper
                if helper2 != helper:
                    printif(f'ANSWER INTERPRETED AS {helper.upper()}')
                try:
                    helper = float(helper)
                    if not (min1 <= helper and helper <= max1):
                        helper += "7" + 7
                except:
                    printif("invalid response, try again")
                    helper = False
            else:
                helper = min1
                skip = True
                prepanswers = givenanswers[:-1]
        else:
            helper = prepanswers[0]
            del prepanswers[0]
            if not (min1 <= helper and max1 >= helper):
                helper = False
            else:
                try:
                    helper += 1
                    helper -= 1
                except:
                    helper = False
    givenanswers.append(helper)
    return helper

import math

def stddnormdistint(z1, z2):
    return (0.5 * (1 + math.erf(z2 / math.sqrt(2)))) - (0.5 * (1 + math.erf(z1 / math.sqrt(2))))

def poissonpmf(k, lambda1):
    k = round(k)
    return (lambda1 ** k) * math.exp(-1 * lambda1) / math.factorial(k)

#all needed functions are now set up, save for database retrieval and usage, which I decided to refrain from using for the first version of this

def mergetest():
    global skip, givenanswers, prepanswers, mergemessage
    skip = False
    givenanswers = []
    printif("\nthere are a lot of approximations in the numbers used for calculations with this program. it will give you confidence at the end, and then you get to make your judgement call.")
    printif("\nthis program was originally designed to make an estimated probability that a merge should be done, but the same process can also apply to attaching records, with the data on the record treated as the other person")
    printif("\nif the answer to a question is unavailable, respond with 'u', if that's an answer. otherwise, give the best answer you can.")
    printif("\notherwise, respond as appropriate with no capitalization of letters or usage of commas in numbers.")
    printif("\nif one person has london as a location and the other has england as a location, it is not considered the same location for this program, even though london is in england.")
    printif("\none typo is considered as a character appearing in the wrong position offsetting others, a character being written or typed as a different character, or a character being omitted")
    printif("\nwhere allowed, 'p' is a partial yes, such as when there are two areas overlapping and you are asked if they are the same place")
    printif("\nyou can also respond with 'undo' to undo a previous response.")
    SCALE = 1
    errorprob = 1 * SCALE
    year = inpnum("what year do you suspect the person was born if it was the same person?", 1600, 1999)
    #popcount is the number of people born around the world in a year in that year range (approximately). Could be off by as much as a factor of 2, but I hope not. Later it is used as how many matching individuals there are.  
    if year < 1700:
        popcount = 7200000
        poprate = 0.048 * SCALE
        urbrate = 0.025
    elif year < 1800:
        popcount = 9400000
        poprate = 0.047 * SCALE
        urbrate = 0.04
    elif year < 1900:
        popcount = 13661000
        poprate = 0.0425 * SCALE
        urbrate = 0.07
    elif year < 1950:
        popcount = 18750000
        poprate = 0.0375 * SCALE
        urbrate = 0.22
    else:
        popcount = 39079000
        poprate = 0.027 * SCALE
        urbrate = 0.39
    popcount *= poprate
    printif(f"\n\tinternal storage data on world population and birth rate have been applied. this is key to knowing how many persons who aren't a match are expected to be at least as similar. {popcount} births are expected per year.")
    helper5000 = inpfor("do both persons have the same location?", ['y', 'n', 'u'])
    if helper5000 == 'n':
        helper5001 = inpfor("is one location inside of the other?", ['y', 'n', 'u', 'p'])
        if helper5001 == 'y':
            popcount = inpnum("what was the approximate population of the larger location at the time?", 10, popcount) * poprate
            printif(f"\n\tthis gives us an update to the population size liable to appear incorrectly as a match. {popcount} viably similar births are expected per year.")
        elif helper5001 == 'n':
            helper5002 = inpfor("is it more likely that one location was used to refer to the other due to being better known?", ['y', 'n'])
            if helper5002 == 'y':
                popcount = inpnum("what was the approximate population of the better known area?", 20, popcount) * poprate / urbrate
                errorprob *= 1 - ((1 - urbrate) ** 2)
                printif(f"\n\texpected viably similar population size has been updated to include the birth of {popcount} people in viably similar space per year, based on birth rates and a stored value for the proportion of people who lived in urban areas at the time. expected chance of observed differences in an actual match has been reduced to {errorprob * 100}%")
            else:
                helper5003 = inpfor("was it more likely moving than a typo?", ['y', 'n'])
                if helper5003 == 'n':
                    if inpfor("was it written instead of typed?", ['y', 'n']) == 'y':
                        errorprob *= 0.05 ** (0.5 + (inpnum("how many typos would be necessary?", 1, 5) / 2))
                        printif(f"\n\texpected chance of observed differences in an actual match has been reduced according to the supposed probability of a written mistake of that level (to {errorprob * 100}%)")
                    else:
                        errorprob *= 0.04 ** (0.5 + (inpnum("how many typos would be necessary?", 1, 5) / 2))
                        printif(f"\n\texpected chance of observed differences in an actual match has been reduced according to the supposed probability of a typed typo of that level (to {errorprob * 100}%).")
                else:
                    helper5004 = inpnum("approxamitely how many days were there between the last confirmation of first confirmed place to the first confirmation of last confirmed place?", 1, 43800)
                    helper5005 = inpnum("approximately what was the population of the latter confirmed place?", 1, popcount)
                    helper5006 = 1
                    helper5007 = 1
                    while helper5007 < 14:
                        helper5006 += poissonpmf(helper5007, helper5004 / 4000)
                        helper5007 += 1
                    popcount = helper5005 * helper5006 * poprate
                    printif(f"\n\texpected non-matches of at least the same similarity has been adjusted to include anyone who was born or moved to the latter place, expecting {popcount} valid births per year")
        elif helper5001 == 'p':
            popcount = inpnum("what is the approximate population of the total combined area?", 10, popcount)
            printif(f"\n\tthis gives us an update to the population size liable to appear incorrectly as a match. {popcount} viably similar births are expected per year.")
    elif helper5000 == 'y':
        popcount = inpnum("what was the approximate population of said location at the time?", 2, popcount) * poprate
        printif(f"\n\tthis gives us an update to the population size liable to appear incorrectly as a match. {popcount} viably similar births are expected per year.")
    # now to check on birthdays. This is already partially factored in, but still not completely. 
    helper5008 = inpnum("over about how many days could either person have been born, including the full range of possibilities for both?", 1, 1000000)
    popcount *= helper5008 / 365
    printif(f"\n\texpected non-matches at least as similar has been changed to match births over that period of time.")
    if popcount < 1 + (helper5008 // 255):
        printif(f'\n\tprobability metrics have just been adjusted to ensure validity if there is an unknown twin or sibling born in the same time frame, raising expectations to {popcount} non-matching persons that are at least as similar.')
        popcount = 1 + (helper5008 // 255)
    ogpopcount = popcount
    minogpopcount = 1 + (helper5008 // 255)
    # now we can handle names. 
    for nameorder in ['first', 'middle', 'last']:
        helper5000 = inpfor(f"do they have the same {nameorder} name?", ['y', 'n', 'u'])
        if helper5000 == 'n':
            proceed = True
            if nameorder == 'last':
                helper5001 = inpfor('is it true that both persons would have been seen as women for purposes of changing last names with marriage?', ['y', 'n', 'u'])
                if not helper5001 == 'n':
                    marriagenamechangerate = 0.4 / 24500
                    if inpfor("were they in the US or a similar country for purposes of marriage counts?", ['y', 'n', 'u']) == 'y':
                        marriagenamechangerate = 1.02 / 24500
                    timevar = inpnum("over about how many days could they have gotten married to produce the difference in last name? if you know they got married, just type 1000000", 5, 1000000)
                    errorprobmultiplier = 0
                    tracker = 1
                    if timevar < 200000:
                        while tracker <= 7:
                            errorprobmultiplier += poissonpmf(tracker, marriagenamechangerate * timevar)
                            tracker += 1
                        if helper5001 == 'u':
                            #just using 0.4 instead of asking if we know either would have been treated as a woman for purposes of taking last names, to ask less questions and be less annoying
                            errorprobmultiplier *= 0.4
                    else:
                        if helper5001 == 'y':
                            errorprob *= 1
                        else:
                            errorprob *= (0.4 + 0.75 * 0.7) / 2
                    if not inpfor("do you know that they were married to someone with the right last name to make the difference?", ['y', 'n']) == 'y':
                        dict5000 = {'very common': 0.04, 'somewhat common': 0.012, 'uncommon': 0.005, 'somewhat rare': 0.002, 'exotic': 0.0001}
                        helper5001 = 'n'
                        for rarity in dict5000.keys():
                            if helper5001 == 'n':
                                helper5001 = inpfor(f"is the new {nameorder} name {rarity} in that place and time?", ['y', 'n'])
                                if helper5001 == 'y':
                                    errorprob *= dict5000[rarity]
                    if errorprobmultiplier != 0:
                        errorprob *= errorprobmultiplier
                    printif(f"\n\texpected chance of observed differences on a match has been reduced to {errorprob * 100}%")
                    proceed = False
            if proceed and inpfor(f'is one {nameorder} name a common variant of the other?', ['y', 'n']) == 'y':
                popcount *= 3.5
                errorprob *= 0.5
                helper5000 = 'y'
                printif("\n\texpected people at least as similar has been increased 250%, and expected chance of observed differences has halved")
            elif proceed and inpfor(f'is one {nameorder} name likely a typo of the other?', ['y', 'n']) == 'y':
                helper5001 = inpnum('how many typos would be necessary?', 1, 5)
                helper5002 = inpfor('was the record the potential typo came from written instead of being typed?', ['y', 'n'])
                if helper5002 == 'y':
                    frequency = 0.075
                else:
                    frequency = 0.02
                errorprob *= poissonpmf(helper5001, frequency)
                helper5000 = 'y'
                printif(f"\n\texpected chance of observed differences has reduced to {errorprob * 100}%.")
        if helper5000 == 'y':
            dict5000 = {'very common': 0.04, 'somewhat common': 0.012, 'uncommon': 0.005, 'somewhat rare': 0.002, 'exotic': 0.0001}
            helper5001 = 'n'
            for rarity in dict5000.keys():
                if helper5001 == 'n':
                    helper5001 = inpfor(f"is that {nameorder} name {rarity} in that place and time?", ['y', 'n'])
                    if helper5001 == 'y':
                        popcount *= dict5000[rarity]
                        printif(f'\n\texpected non-matching people has been reduced according to name rarity, ({dict5000[rarity] * 100}% of people are treated as having any given {rarity} name).')
            if helper5001 == 'n':
                printif('\n\tmetrics have not been adjusted due to lack of an accepted name rarity.')
    helper5000 = inpfor('are both person profiles confirmed to be the same gender or the same sex by at least one source?', ['y', 'n'])
    if helper5000 == 'y':
        popcount /= 2
        knownsex = True
        printif(f'\n\tthe expected size of the group of non-matching people at least as similar is now {popcount} people')
    else:
        knownsex = False
    helper5000n = inpfor('do you have a date range on the death date of both?', ['n', 'y'])
    if helper5000n == 'y':
        helper5001n = inpnum('what year do you think they died if it was the same person?', year, year + 130) // 1
        helper5002n = inpnum('over how many days could either have died?', 1, 365 * 30)
        helper5003n = inpfor('did their county have a relatively high life expectancy compared to others globally?', ['y', 'n', 'u'])
        if helper5003n == 'y':
            helper5003n = 'high'
        elif helper5003n == 'n':
            helper5003n = 'low'
        else:
            helper5003n = 'mid'
        deathsimprob = f(year, helper5001n, helper5003n) * helper5002n / 365.25
        popcount *= deathsimprob
        printif(f"\n\texpected people at least as similar multiplied by a factor of {deathsimprob} for death time related data; that's a decent estimate for the probability of that amount of similarity")
    helper5000 = inpfor('at a glance, do parents, grandparents, etc seem to match up insomuch as they are present?', ['y', 'n'])
    if helper5000 == 'n':
        helper5001 = inpnum("how many between the mother and father's sides don't seem to match up insomuch as they exist?", 1, 2)
        errorprob *= 0.35 ** helper5001
        if helper5001 == 2:
            errorprob /= 3
        printif(f"\n\tchance of observed differences has been adjusted to account for the difference being made by divorces and remarriages based on more general population statistics{['', ', and even further because it was both parents'][round(helper5001 - 1)]}")
    else:
        printif("\nthis is great, and we can factor this in soon.")
    helper5000 = inpfor('at a glance, do descendants AND spouses seem to match up insomuch as they are added?', ['y', 'n'])
    if helper5000 == 'n':
        errorprob *= 0.35
        printif(f"\n\tchance of observed differences has been adjusted to account for the difference being made by divorces and remarriages and the like based on more general popuation statistics")
    else:
        printif("\nthis is great, and we can factor this in if you want.")
    relativesdone = []
    printif("\nnow we can begin doing relatives, including siblings if you want to add them")
    offspringdone = 0
    while inpfor(f'would you like to do one more relative (you have done {relativesdone})', ['n', 'y']) == 'y':
        relativesdone.append(inpforany('what relative next?'))
        #location handling
        printif("\nlocation data for relatives is mostly irrelevant for this purpose, as long as it makes sense. be sure to look into the locations just to see that everything checks out. if they don't, there may be necessary corrections to faulty work, or you may find solid evidence against a match. the birth sex and gender of relatives also isn't applied here, partially so spouse names can be implemented to family.")
        #birthday handling
        helper6000 = inpfor(f"the only birthdays we apply to calculation here are birth parents and birth children. is {relativesdone[-1]} among them?", ['n', 'y'])
        if helper6000 == 'y':
            helper6000 = inpfor("is the relationship mother/child, father/child, or parent/child", ['mother', 'father', 'parent'])
            helpmean = {'mother': 28.5 * 365.25, 'father': 34 * 365.25, 'parent': (28.5 + 34) * 365.25 * 0.5}[helper6000]
            helpstdd = {'mother': 7 * 365.25, 'father': 9 * 365.25, 'parent': (math.sqrt(49 + 81) + 2.75) * 365.25}[helper6000]
            helper6001 = inpnum(f"what year was {relativesdone[-1]} born at earliest", 1500, 2025)
            helper6002 = inpnum(f"how many days of possible birth variation over both versions of {relativesdone[-1]}", 1, 1000000)
            helper6003 = [364.25 * (year - helper6001)]
            helper6003.append(helper6003[0] + helper6002)
            if helper6003[0] < 0:
                helper6003[0] *= 0 - 1
            helper6003[0] = (helper6003[0] - helpmean) / helpstdd
            if helper6003[1] < 0:
                helper6003[1] *= 0 - 1
            helper6003[1] = (helper6003[1] - helpmean) / helpstdd
            helper6004 = stddnormdistint(min(helper6003), max(helper6003))
            #multiply popcount if it makes sense given ogpopcount and minogpopcount
            helpbool1 = inpfor(f"would {relativesdone[-1]} be the {helper6000} in the {helper6000}/child relationship?", ['y', 'n'])
            if helpbool1 == 'y':
                if ogpopcount * helper6004 < minogpopcount:
                    popcount *= minogpopcount / ogpopcount
                    ogpopcount = minogpopcount
                    printif('\ncalculation cap for unknown sibling or twin validity applies')
                    if not prepanswers:
                        prepanswers = ['u', 'u', 'u']
                else:
                    popcount *= helper6004
                    ogpopcount *= helper6004
            else:
                if knownsex:
                    offspringdone += 1
                    popcount *= helper6004
                else:
                    printif('\nsince you did not confirm a known sex, children do not apply this time with this program (to avoid confusion with spouse).')
                    if not prepanswers:
                        prepanswers = ['u', 'u', 'u']
        #name handling
        for nameorder in ['first', 'middle', 'last']:
            helper5000 = inpfor(f"do both {relativesdone[-1]}'s {nameorder} names match?", ['y', 'n', 'u'])
            wasn = False
            if helper5000 == 'n':
                wasn = True
                proceed = True
                if nameorder == 'last':
                    if not inpfor(f'does {relativesdone[-1]} have the same passed down last name with the same origin as a prior entry?', ['y', 'n']) == 'y':
                        helper5001 = inpfor(f'is it true that both {relativesdone[-1]}s would have been seen as women for purposes of changing last names with marriage?', ['y', 'n', 'u'])
                        if not helper5001 == 'n':
                            marriagenamechangerate = 0.4 / 24500
                            if inpfor(f"was {relativesdone[-1]} in the US or a similar country for purposes of overall marriage counts?", ['y', 'n', 'u']) == 'y':
                                marriagenamechangerate = 1.02 / 24500
                            timevar = inpnum(f"over about how many days could {relativesdone[-1]} have gotten married to produce the difference in last name? if you know they got married, or if the last names could be variants of each other, just type a 1000000", 5, 1000000)
                            errorprobmultiplier = 0
                            tracker = 1
                            if timevar < 200000:
                                while tracker <= 7:
                                    errorprobmultiplier += poissonpmf(tracker, marriagenamechangerate * timevar)
                                    tracker += 1
                                if helper5001 == 'u':
                                    #just using 0.4 instead of asking if we know either would have been treated as a woman for purposes of taking last names, to ask less questions and be less annoying
                                    errorprobmultiplier *= 0.4
                            else:
                                if helper5001 == 'y':
                                    errorprob *= 1
                                else:
                                    errorprob *= (0.4 + 0.75 * 0.7) / 2
                            if not inpfor("is the right last name to make the difference a given?", ['y', 'n', 'u']) == 'y':
                                dict5000 = {'very common': 0.04, 'somewhat common': 0.012, 'uncommon': 0.005, 'somewhat rare': 0.002, 'exotic': 0.0001}
                                helper5001 = 'n'
                                for rarity in dict5000.keys():
                                    if helper5001 == 'n':
                                        helper5001 = inpfor(f"is the new {nameorder} name {rarity} in that place and time?", ['y', 'n'])
                                        if helper5001 == 'y':
                                            errorprob *= dict5000[rarity]
                            if errorprobmultiplier != 0:
                                errorprob *= errorprobmultiplier
                            proceed = False
                    else:
                        proceed = False
                        errorprob *= 0.4
                if proceed and inpfor(f"is one {relativesdone[-1]}'s {nameorder} name a common variant of the other?", ['y', 'n']) == 'y':
                    popcount *= 3.5
                    helper5000 = 'y'
                elif proceed and inpfor(f"is one {relativesdone[-1]}'s {nameorder} name likely a typo of the other?", ['y', 'n']) == 'y':
                    helper5001 = inpnum('how many typos would be necessary?', 1, 5)
                    helper5002 = inpfor('was the record the potential typo came from written instead of being typed?', ['y', 'n'])
                    if helper5002 == 'y':
                        frequency = 0.075
                    else:
                        frequency = 0.02
                    errorprob *= poissonpmf(helper5001, frequency)
                    helper5000 = 'y'
            if helper5000 == 'y' and (nameorder != 'last' or ((not wasn) and not inpfor(f'does {relativesdone[-1]} have the same passed down last name with the same origin as a prior entry?', ['y', 'n']) == 'y')):
                dict5000 = {'very common': 0.04, 'somewhat common': 0.012, 'uncommon': 0.005, 'somewhat rare': 0.002, 'exotic': 0.0001}
                if nameorder != 'last' and inpfor(f"does {relativesdone[-1]}'s {nameorder} name commonly appear in the family", ['y', 'n']) == 'y':
                    dict5000 = {'very common': 0.2}
                    popcount *= 0.2
                else:
                    helper5001 = 'n'
                    for rarity in dict5000.keys():
                        if helper5001 == 'n':
                            helper5001 = inpfor(f"is that {nameorder} name {rarity} in that place and time?", ['y', 'n'])
                            if helper5001 == 'y':
                                if ogpopcount * dict5000[rarity] < minogpopcount:
                                    popcount *= minogpopcount / ogpopcount
                                    ogpopcount = minogpopcount
                                    printif('\ncalculation caps on non-personal data impacts apply')
                                else:
                                    popcount *= dict5000[rarity]
                                    ogpopcount *= dict5000[rarity]
        printif(f"\n\tafter that relative data, the expected chance of observed differences in a match is {errorprob * 100}%, and the expected number of people that aren't matches and appear at least as similar is {popcount}")
    #correction for unordered offspring
    if ogpopcount != minogpopcount:
        popcount *= math.factorial(int(inpfor('how many of the direct offspring you incorporated in the calculation were you unsure of the orders of birth for?', [f'{x}' for x in range(0, offspringdone + 1)])))
        printif(f'the fact that sibling order was undetermined to this extent means there are possibilities with the same children names in a different order on another family; things have been adjusted accordingly.')
    #final confidence calculation
    confidence = errorprob / (errorprob + popcount)
    printif("\n\n\tfinal confidence is calculated as the proportion of expected possible cases where it is a match and observed differnces happened in accordance with chance instead of someone else being similar enough to appear as similar or more. Cases in which multiple non-matches are at least as similar have a larger weight on the resulting number than they would in probability, but the difference should be small in cases where it is very likely that it's a match. Better safe than sorry, especially when you risk five people being merged into one.")
    printif(f"\n\n\n\nbased on your answers, this program is {confidence * 100}% confident that the two person files match the same person.")
    if confidence >= 0.999:
        printif("\nthis means it is recomended that you merge them or attach the record.")
    else:
        printif("\nthis means that this program is not confident enough to suggest you merge them or attach the record yet, based on your answers.")
    printif(f"\n\n\n\nif you do merge or attach the file, you may copy/paste this message and add additional thoughts at the end when explaining why your decision is correct:")
    printif(f"\tI used a program called should_you_merge to calculate a confidence percentage that merging or attaching the file was correct, based on multiple heuristics (name similarity, life frame similarities, family data, etc.) and my own inputs. My series of inputs in response to the questions of the program was {givenanswers}, which resulted in {confidence * 100}% confidence based on that part of my evaluation alone. To verify my inputs were correct or get any comparative information available by my question/answer pairs to undo what I did (in case I was wrong), you can find the same program on https://github.com/jackhfamilyhist/should_you_merge, which will complete and give the same confidence with the same question/answer pairs after you finish repeating my inputs, provided you're using the same version I did. Any evidence I saw (if any) that wasn't included in the calculation, when combined with the calculated confidence, resulted in me merging.")
    printif('\n')

try:
    mergetest()
except Exception as e:
    print(f"{e}")
    import traceback
    traceback.print_exc()
    skip = False
    prepanswers = []
    helper9 = inpfor('are you using the most recently released version of should_you_merge on https://github.com/jackhfamilyhist/should_you_merge?', ['y', 'n'])
    if helper9 == 'y':
        input(linefit("\ntext (208) 412-7410 to alert the developer to the error you've experienced. \nit should then be fixed in the next version, which could realistically be out in less than a week."))
    else:
        input(linefit('please replace with the latest version and see if your error still exists'))

helper92 = skip or input(linefit("press enter to close program, or input something else to run it again  "))
while helper92:
    try:
        if helper92 == 'undo':
            prepanswers = givenanswers[:-1]
        mergetest()
        helper92 = skip or input(linefit("press enter to close program, or input something else to run it again  "))
    except Exception as e:
        print(f"{e}")
        import traceback
        traceback.print_exc()
        helper9 = inpfor('are you using the most recently released version of should_you_merge on https://github.com/jackhfamilyhist/should_you_merge?', ['y', 'n'])
        if helper9 == 'y':
            input(linefit("\ntext (208) 412-7410 to alert the developer to the error you've experienced. \nit should then be fixed in the next version, which could realistically be out in less than a week."))
        else:
            input(linefit('please replace with the latest version and see if your error still exists'))

