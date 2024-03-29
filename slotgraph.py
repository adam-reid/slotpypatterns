#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Use some data mining patterns to try to find matching patterns.
"""
import argparse
import functools
import itertools
import random
import timeit

from collections import Counter, namedtuple

# Globals.. normally class-member variables, global for testing.
rng_seed = 42  # rng seed.
symbols = [chr(65 + i) for i in range(10)]  # get first 10 characters as symbols
reels = 5  # number of reels on screen
rows = 3  # number of rows on screen

# A node has position coordinates and an associated symbol.
# Eg (3,1) is positioned at reel 3, column 1.
Node = namedtuple("Node", ["x", "y", "symbol"])


def show_screen(screen, pattern=None):
    """
    Prints the symbols indicated in the pattern for the screen.
    If no pattern is provided, all symbols are displayed.

    :param screen: the 2d screen list for displaying
    :param pattern: the pattern to match. Default: None
    """
    for row, symbols in enumerate(screen):
        for column, symbol in enumerate(symbols):
            c = symbol if pattern is None or Node(column, row, symbol) in pattern else '-'
            print(c, end=' ')
        print()
    print()


def show_me(screen_hits, screen):
    """
    Prints the symbols indicated in screen_hits for the screen given.
    Pauses between screens are resumed with 'enter'.

    :param screen_hits: a list of a set of (x,y) nodes.
    :param screen: the screen to render.
    """
    for pattern in screen_hits:
        show_screen(screen, pattern)
        input(pattern)


def grow(node_list):
    """
    Takes a list of sets of nodes, finds all combinations, and saves
    valid pairings.

    :param node_list: a list of sets of nodes for making combinations.
    :return: a new unique list of sets of nodes.
    """
    new_list = []

    for s1, s2 in itertools.combinations(node_list, 2):
        new_set = {*s1, *s2}
        target_length = len(s1) + 1  # should only grow by 1 node.

        if len(new_set) == target_length and new_set not in new_list:
            new_list.append(new_set)

    return new_list


def prune(set_list):
    """
    Prunes combinations that are not identical in symbols.

    :param set_list: the list of sets containing nodes.
    :return the pruned list
    """
    symbol_set_list = [{symbol for _, _, symbol in current_set} for current_set in set_list]
    return [sl for _, sl in list(filter(lambda t: len(t[0]) == 1, zip(symbol_set_list, set_list)))]


def apriori(screen, min_support, demo=False):
    """
    Uses the apriori algorithm to grow a frequent pattern tree.

    Note: This uses min support as a means to bootstrap the filtering.
    This is not truly using the minimum support, as this evaluator 
    doesn't necessarily need to check minimum support as the tree grows.

    Rather, the minimum support is used to check the initial condition for
    nodes worth pursuing; then, it is used to determine the stopping point
    of the growth.

    :param screen: the screen to mine.
    :param min_support: the minimum support value.
    :param demo: whether to run demo mode or not. Default: False.
    :return: the 5-node pattern list.
    """
    # Resolving nodes
    nodes = [Node(x, y, symbol) for y, symbols in enumerate(screen) for x, symbol in enumerate(symbols)]

    # Count nodes.
    symbols = [node.symbol for node in nodes]
    db = {symbol: symbols.count(symbol) for symbol in symbols}
    final = dict(filter(lambda kv: kv[1] >= min_support, db.items()))

    # Filter out notes not meeting the minimum support
    nodes = [node for node in nodes if node.symbol in final]

    if min_support == 1:
        return nodes

    pattern_list = []

    # Resolving pairs
    for n1, n2 in itertools.combinations(nodes, 2):
        match_down = (n1.x == n2.x and n1.y == n2.y-1)
        match_right = (n1.x == n2.x-1 and n1.y == n2.y)

        if match_right or match_down:
            pattern_list.append({n1, n2})

    pattern_list = prune(pattern_list)

    # The rest is iterative.
    for i in range(2, min_support):
        pattern_list = grow(pattern_list)
        pattern_list = prune(pattern_list)

        if demo:
            print(f'Found {len(pattern_list)} {i+1}-item matches!')

    return pattern_list


def generate_screen(demo=False):
    """
    Either generates a random screen using the global parameters from earlier,
    or creates a static screen when demo is True.

    :param demo: flag to use the demo / static screen or not. Default: False.
    :return: the screen 2-d list
    """
    if demo:
        screen = [
            ['A', 'A', 'A', 'A', 'F'],
            ['B', 'B', 'A', 'F', 'F'],
            ['A', 'B', 'F', 'F', 'B']
        ]
    else:
        global reels
        global rows
        global symbols

        screen = [[random.choice(symbols) for reel in range(reels)] for row in range(rows)]

    return screen


def test_drive(func, demo, number, min_support):
    """
    Wrapper for the function. Will either demo the func, or time it.

    :param func: the function to test drive
    :param demo: boolean of whether to demo or time. True=demo.
    :param number: the number of simulations to use when timing.
    """
    if demo:
        screen = generate_screen(demo)
        show_screen(screen)
        result = func(screen, min_support, demo)
        show_me(result, screen)
    else:
        global rng_seed
        random.seed(rng_seed)
        s = timeit.timeit(functools.partial(func, generate_screen(), min_support), number=number)
        print(f'Ran {func.__qualname__} for {number} simulations in {s} seconds.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apriori test with min support for slot-game pattern matching")
    parser.add_argument('-d', '--demo', action='store_true', help="Flag to set as demo or not", )
    parser.add_argument('-n', '--number', type=int, default=1_000_000, help="Number of simulations to run [Default: 1,000,000]", )
    parser.add_argument('-m', '--min-support', type=int, default=5, help="The minimum support value [Default: 5].")
    args = parser.parse_args()

    test_drive(apriori, args.demo, args.number, args.min_support)
