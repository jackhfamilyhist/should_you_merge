prepanswers = []
givenanswers = []
skip = False

def inpfor(prompt, answers):
    global prepanswers, givenanswers, skip
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
                choice = input(helper2).lower()
                if not choice in (answers + ['undo']):
                    printif("invalid response, try again.")
        if choice != 'undo':
            givenanswers.append(choice)
        else:
            prepanswers = givenanswers[:-1]
            skip = True
            choice = answers[0].lower()
            if not prepanswers:
                prepanswers.append(0)
    else:
        choice = answers[0].lower()
    return choice

def printif(text1):
    global prepanswers, skip
    if not skip:
        if not prepanswers:
            print(text1)

def inpnum(prompt, min1, max1):
    global prepanswers, givenanswers, skip
    helper = skip
    while not helper:
        if not prepanswers:
            helper = input(f"{'\n\n' + prompt}  number answer, no commas:  ")
            if not helper.lower() == 'undo':
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

def poissonpmf(k, lambda1):
    k = round(k)
    return (lambda1 ** k) * math.exp(-1 * lambda1) / math.factorial(k)

#all needed functions are now set up, save for database retrieval and usage, which I decided to refrain from using for the first version of this

def mergetest():
    global skip, givenanswers, prepanswers
    skip = False
    givenanswers = []
    printif("\nthere are a lot of approximations in the numbers used for calculations with this program. It will give you confidence at the end, and then you get to make your judgement call.")
    printif("\nif the answer to a question is unavailable, respond with 'u'.")
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
    helper5000 = inpfor("do both persons have the same location?", ['y', 'n', 'u'])
    if helper5000 == 'n':
        helper5001 = inpfor("is one location inside of the other?", ['y', 'n', 'u', 'p'])
        if helper5001 == 'y':
            popcount = inpnum("what was the approximate population of the larger location at the time?", 10, popcount) * poprate
        elif helper5001 == 'n':
            helper5002 = inpfor("is it more likely that one location was used to refer to the other due to being better known?", ['y', 'n'])
            if helper5002 == 'y':
                popcount = inpnum("what was the approximate population of the better known area?", 100, popcount) * poprate / urbrate
            else:
                helper5003 = inpfor("was it more likely moving than a typo?", ['y', 'n'])
                if helper5003 == 'n':
                    if inpfor("was it written instead of typed?", ['y', 'n']) == 'y':
                        errorprob *= 0.05 ** inpnum("how many typos would be necessary?", 1, 5)
                    else:
                        errorprob *= 0.04 ** inpnum("how many typos would be necessary?", 1, 5)
                else:
                    helper5004 = inpnum("approxamitely how many days were there between the last confirmation of first confirmed residence to the first confirmation of last confirmed residence?", 1, 43800)
                    helper5005 = inpnum("approximately what was the population of the latter confirmed area of residence?", 1, popcount)
                    helper5006 = 1
                    helper5007 = 1
                    while helper5007 < 14:
                        helper5006 += poissonpmf(helper5007, helper5004 / 4000)
                        helper5007 += 1
                    popcount = helper5005 * helper5006 * poprate
        elif helper5001 == 'p':
            popcount = inpnum("what is the approximate population of the combined area?", 10, popcount)
    elif helper5000 == 'y':
        popcount = inpnum("what was the approximate population of said location at the time?", 2, popcount) * poprate
    # now to check on birthdays. This is already partially factored in, but still not completely. 
    popcount *= inpnum("over about how many days could either person have been born, including the full range of possibilities for both?", 1, 1000000) / 365
    # now we can handle names. 
    for nameorder in ['first', 'middle', 'last']:
        helper5000 = inpfor(f"do they have the same {nameorder} name?", ['y', 'n', 'u'])
        if helper5000 == 'n':
            proceed = True
            if nameorder == 'last':
                helper5001 = inpfor('is it true that both persons would have been seen as women for purposes of changing last names with marriage?', ['y', 'n', 'u'])
                if not helper5001 == 'n':
                    marriagenamechangerate = 0.4 / 24500
                    if inpfor("were they in the US or a similar country for purposes of marriage counts and last name changes?", ['y', 'n', 'u']) == 'y':
                        marriagenamechangerate = 1.02 / 24500
                    timevar = inpnum("over about how many days could they have gotten married to produce the difference in last name? if you know they got married, or if the last names could be variants of each other, just type a 1000000", 5, 1000000)
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
                    proceed = False
            if proceed and inpfor(f'is one {nameorder} name a common variant of the other?', ['y', 'n']) == 'y':
                popcount *= 3.5
                helper5000 = 'y'
            elif proceed and inpfor(f'is one {nameorder} name likely a typo of the other?', ['y', 'n']) == 'y':
                helper5001 = inpnum('how many typos would be necessary?', 1, 5)
                helper5002 = inpfor('was the record the potential typo came from written instead of being typed?', ['y', 'n'])
                if helper5002 == 'y':
                    frequency = 0.075
                else:
                    frequency = 0.02
                errorprob *= poissonpmf(helper5001, frequency)
                helper5000 = 'y'
        if helper5000 == 'y':
            dict5000 = {'very common': 0.04, 'somewhat common': 0.012, 'uncommon': 0.005, 'somewhat rare': 0.002, 'exotic': 0.0001}
            helper5001 = 'n'
            for rarity in dict5000.keys():
                if helper5001 == 'n':
                    helper5001 = inpfor(f"is that {nameorder} name {rarity} in that place and time?", ['y', 'n'])
                    if helper5001 == 'y':
                        popcount *= dict5000[rarity]
    helper5000 = inpfor('are both person profiles confirmed to be the same gender or the same sex by at least one source?', ['y', 'n'])
    if helper5000 == 'y':
        popcount /= 2
    helper5000 = inpfor('at a glance, do parents, grandparents, etc seem to match up insomuch as they are present?', ['y', 'n'])
    if helper5000 == 'n':
        helper5001 = inpnum("how many between the mother and father's sides don't seem to match up insomuch as they exist?", 1, 2)
        errorprob *= 0.35 ** helper5001
        if helper5001 == 2:
            errorprob /= 3
    else:
        printif("\nthis is great, but can't be factored in too much with this program, since that would be very difficult to factor in positively the right amount. the number of questions that you'd have to answer to bring it in would also be astronomical. just know you can be as much more confident than this program says it is as you can see with the matches.")
    helper5000 = inpfor('at a glance, do descendants and spouses seem to match up insomuch as they are added?', ['y', 'n'])
    if helper5000 == 'n':
        errorprob *= 0.35
    else:
        printif("\nthis is great, but can't be factored in too much with this program, since that would be very difficult to factor in positively the right amount. the number of questions that you'd have to answer to bring it in would also be astronomical. just know you can be as much more confident than this program says it is as you can see with the matches.")
    confidence = errorprob / (errorprob + popcount)
    printif(f"\n\n\n\nbased on your answers, this program is {confidence * 100}% confident that the two person files should be merged.")
    if confidence >= 0.999:
        printif("\nthis means it is recomended that you merge them.")
    else:
        printif("\nthis means that this program is not confident enough to suggest you merge them yet, based on your answers.")

try:
    mergetest()
except Exception as e:
    print(f"{e}")
    import traceback
    traceback.print_exc()


while skip or input("press enter to close program, or input something else to run it again  "):
    try:
        mergetest()
    except Exception as e:
        print(f"{e}")
        import traceback
        traceback.print_exc()

