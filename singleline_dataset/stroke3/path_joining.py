# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/05a_path_joining.ipynb.

# %% auto 0
__all__ = ['join_2_strokes', 'select_2_strokes', 'join_endpoints', 'closest_endpoint_pair', 'merge_closest_strokes',
           'merge_until', 'splice_2_strokes', 'join_splice', 'splice_until']

# %% ../../nbs/05a_path_joining.ipynb 2
import copy

import numpy as np

# %% ../../nbs/05a_path_joining.ipynb 16
def join_2_strokes(lhs, l_pos, rhs, r_pos):
    to_join = None
    if l_pos == START:
        if r_pos == START:
            to_join = [np.flip(rhs, axis=0), lhs]
        elif r_pos == END:
            to_join = [rhs, lhs]
        else:
            raise Exception(f"invalid r_pos: {r_pos}")
    elif l_pos == END:
        if r_pos == START:
            to_join = [lhs, rhs]
        elif r_pos == END:
            to_join = [lhs, np.flip(rhs, axis=0)]
        else:
            raise Exception(f"invalid r_pos: {r_pos}")
    else:
        raise Exception(f"invalid l_pos: {l_pos}")
    return np.concatenate(to_join, axis=0)

# %% ../../nbs/05a_path_joining.ipynb 19
def select_2_strokes(strokes, l_idx, r_idx):
    lhs = strokes[l_idx]
    rhs = strokes[r_idx]
    remaining = [x for i, x in enumerate(strokes) if i not in [l_idx, r_idx]]
    return lhs, rhs, remaining


def join_endpoints(strokes, l_idx, l_pos, r_idx, r_pos):
    lhs, rhs, remaining = select_2_strokes(strokes, l_idx, r_idx)
    joined = join_2_strokes(lhs, l_pos, rhs, r_pos)
    return [joined] + remaining

# %% ../../nbs/05a_path_joining.ipynb 22
def closest_endpoint_pair(strokes):
    min_dist = 1e10
    l_idx = None
    r_idx = None
    l_pos = None
    r_pos = None

    for i, lhs in enumerate(strokes):
        for j, rhs in enumerate(strokes):
            if i == j:
                continue

            l0_r0_dist = np.linalg.norm(lhs[START] - rhs[START])
            l0_r1_dist = np.linalg.norm(lhs[START] - rhs[END])
            l1_r0_dist = np.linalg.norm(lhs[END] - rhs[START])
            l1_r1_dist = np.linalg.norm(lhs[END] - rhs[END])

            # print(i, len(c), (l0_r0_dist, l0_r1_dist, l1_r0_dist, l1_r1_dist))

            if l0_r0_dist < min_dist:
                min_dist = l0_r0_dist
                l_idx = i
                r_idx = j
                l_pos = START
                r_pos = START
            if l0_r1_dist < min_dist:
                min_dist = l0_r1_dist
                l_idx = i
                r_idx = j
                l_pos = START
                r_pos = END
            if l1_r0_dist < min_dist:
                min_dist = l1_r0_dist
                l_idx = i
                r_idx = j
                l_pos = END
                r_pos = START
            if l1_r1_dist < min_dist:
                min_dist = l1_r1_dist
                l_idx = i
                r_idx = j
                l_pos = END
                r_pos = END
    return min_dist, l_idx, l_pos, r_idx, r_pos

# %% ../../nbs/05a_path_joining.ipynb 24
def merge_closest_strokes(strokes, dist_threshold=10.0):
    sorted_strokes = sorted(strokes, key=lambda s: len(s), reverse=True)

    min_dist, min_l_idx, min_l_pos, min_r_idx, min_r_pos = closest_endpoint_pair(
        sorted_strokes
    )

    print(f"Minimum distance: {min_dist}")
    print(f"From {min_l_idx}_{min_l_pos} ({len(strokes[min_l_idx])} points)")
    print(f"To {min_r_idx}_{min_r_pos} ({len(strokes[min_l_idx])} points)")

    if min_dist >= dist_threshold:
        print("not merging")
        return min_dist, strokes

    return min_dist, join_endpoints(
        sorted_strokes, min_l_idx, min_l_pos, min_r_idx, min_r_pos
    )

# %% ../../nbs/05a_path_joining.ipynb 26
def merge_until(strokes, dist_threshold=10.0):
    curr_strokes = copy.copy(strokes)
    all_iterations = [curr_strokes]
    for i in range(len(curr_strokes)):
        min_dist, curr_strokes = merge_closest_strokes(
            curr_strokes, dist_threshold=dist_threshold
        )
        print(f"[{i}] - len(curr_strokes) = {len(curr_strokes)}, min_dist = {min_dist}")
        if min_dist > dist_threshold:
            print("exceeded dist threshold")
            break
        all_iterations.append(curr_strokes)
    print(
        f"finished merging - len(curr_strokes) = {len(curr_strokes)}, min_dist = {min_dist}"
    )
    return curr_strokes, all_iterations

# %% ../../nbs/05a_path_joining.ipynb 31
def splice_2_strokes(lhs, rhs, k):
    return np.concatenate([rhs[:k], lhs, rhs[k:]], axis=0)


def join_splice(strokes, l_idx, r_idx, k):
    lhs, rhs, remaining = select_2_strokes(strokes, l_idx, r_idx)
    joined = splice_2_strokes(lhs, rhs, k)
    return [joined] + remaining


# | export
def splice_until(strokes, dist_threshold=10.0):
    curr_strokes = copy.copy(strokes)
    all_iterations = [curr_strokes]
    for i in range(len(curr_strokes)):
        min_dist, min_l_idx, min_r_idx, k = closest_splice_pair(curr_strokes)

        curr_strokes = join_splice(curr_strokes, min_l_idx, min_r_idx, k)

        print(f"Minimum distance: {min_dist}")
        print(f"From {min_l_idx} ({len(strokes[min_l_idx])} points)")
        print(f"To {min_r_idx} ({len(strokes[min_l_idx])} points)")
        print(f"At index k={k}")

        if min_dist > dist_threshold:
            print("exceeded dist threshold")
            break
        all_iterations.append(curr_strokes)
    print(
        f"finished merging - len(curr_strokes) = {len(curr_strokes)}, min_dist = {min_dist}"
    )
    return curr_strokes, all_iterations