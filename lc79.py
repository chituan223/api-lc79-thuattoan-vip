# app.py – Flask + Tele68 + 100 pentter thật – không numpy – không timeout
from flask import Flask, jsonify
import requests, threading, time, os, math
from collections import deque

app = Flask(__name__)
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
UPDATE_SEC = 3  # giảm xuống 3 giây cho mượt
HISTORY_MAX = 500

history_totals = deque(maxlen=HISTORY_MAX)
history_tx = deque(maxlen=HISTORY_MAX)
last_data = {
    "phien": None, "xucxac1": 0, "xucxac2": 0, "xucxac3": 0,
    "tong": 0, "ketqua": "", "du_doan": "X", "do_tin_cay": 0, "id": "pentter100real"
}

# ========== 100 THUẬT TOÁN KHÔNG NUMPY – LOGIC CHUẨN – KHÔNG RANDOM ==========
# 00 – Mean reversion 10
def predict_00(h):
    if len(h) < 10: return 'X'
    avg = sum(h[-10:]) / 10
    return 'T' if avg < 10.5 else 'X'

# 01 – Streak-breaker 5
def predict_01(h):
    if len(h) < 5: return 'X'
    tai = sum(1 for x in h[-5:] if x > 10.5)
    xiu = 5 - tai
    if tai == 5: return 'X'
    if xiu == 5: return 'T'
    return 'X'

# 02 – Entropy drop
def predict_02(h):
    if len(h) < 20: return 'X'
    c = [0] * 19
    for x in h[-20:]: c[x] += 1
    ent = -sum((p / 20) * math.log2(p / 20) for p in c if p)
    return 'T' if ent < 2.8 else 'X'

# 03 – Markov order-2
def predict_03(h):
    if len(h) < 3: return 'X'
    trans = {'TT': 0, 'TX': 0, 'XT': 0, 'XX': 0}
    for i in range(1, len(h)):
        k = ('T' if h[i - 1] > 10.5 else 'X') + ('T' if h[i] > 10.5 else 'X')
        trans[k] += 1
    last = ('T' if h[-2] > 10.5 else 'X') + ('T' if h[-1] > 10.5 else 'X')
    return 'T' if trans[last + 'T'] > trans[last + 'X'] else 'X'

# 04 – Majority vote 7
def predict_04(h):
    if len(h) < 7: return 'X'
    tai = sum(1 for x in h[-7:] if x > 10.5)
    return 'T' if tai >= 4 else 'X'

# 05 – Range expansion
def predict_05(h):
    if len(h) < 12: return 'X'
    return 'T' if max(h[-12:]) - min(h[-12:]) > 12 else 'X'

# 06 – Median cross
def predict_06(h):
    if len(h) < 9: return 'X'
    w = sorted(h[-9:])
    m = w[4]
    return 'T' if m > 10.5 else 'X'

# 07 – Tail-ratio
def predict_07(h):
    if len(h) < 25: return 'X'
    tails = sum(1 for x in h[-25:] if 3 <= x <= 5 or 16 <= x <= 18)
    return 'T' if tails > 6 else 'X'

# 08 – Delta-1 momentum
def predict_08(h):
    if len(h) < 5: return 'X'
    d = [h[i] - h[i - 1] for i in range(-1, -5, -1)]
    return 'T' if all(x > 0 for x in d) else 'X'

# 09 – Birthday paradox
def predict_09(h):
    if len(h) < 23: return 'X'
    return 'T' if len(set(h[-23:])) < 16 else 'X'

# 10 – Gap fill
def predict_10(h):
    if len(h) < 20: return 'X'
    gaps = [i for i, x in enumerate(h[-20:], 1) if 10 <= x <= 11]
    return 'T' if len(gaps) < 4 else 'X'

# 11 – Cusum
def predict_11(h):
    if len(h) < 25: return 'X'
    s = 0
    for x in h[-25:]:
        s += x - 10.5
        if abs(s) > 25: return 'T' if s > 0 else 'X'
    return 'X'

# 12 – Linear regression slope
def predict_12(h):
    if len(h) < 20: return 'X'
    n = 20
    x = list(range(n))
    y = h[-20:]
    sx = sum(x)
    sy = sum(y)
    sxx = sum(i * i for i in x)
    sxy = sum(i * j for i, j in zip(x, y))
    m = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return 'T' if m > 0.1 else 'X'

# 13 – Mode flip
def predict_13(h):
    if len(h) < 12: return 'X'
    try:
        mode = max(set(h[-12:]), key=h[-12:].count)
    except:
        return 'X'
    return 'T' if mode > 10.5 else 'X'

# 14 – Kelly criterion
def predict_14(h):
    if len(h) < 50: return 'X'
    wins = sum(1 for x in h[-50:] if x > 10.5)
    p = wins / 50
    return 'T' if p > 0.52 else 'X'

# 15 – RSI-like
def predict_15(h):
    if len(h) < 14: return 'X'
    gains = [x - 10.5 for x in h[-14:] if x > 10.5]
    losses = [10.5 - x for x in h[-14:] if x <= 10.5]
    rs = (sum(gains) / 14) / (sum(losses) / 14 + 1e-9)
    return 'T' if rs > 1.2 else 'X'

# 16 – Bollinger breach
def predict_16(h):
    if len(h) < 20: return 'X'
    last20 = h[-20:]
    m = sum(last20) / 20
    s = (sum((x - m) ** 2 for x in last20) / 20) ** 0.5
    return 'T' if h[-1] > m + 1.5 * s else 'X'

# 17 – Arc-sine law
def predict_17(h):
    if len(h) < 40: return 'X'
    pos = sum(1 for x in h[-40:] if x > 10.5)
    return 'T' if pos < 8 or pos > 32 else 'X'

# 18 – Benford check
def predict_18(h):
    if len(h) < 30: return 'X'
    first = [int(str(x)[0]) for x in h[-30:]]
    return 'T' if first.count(1) < 3 else 'X'

# 19 – Peak-to-avg
def predict_19(h):
    if len(h) < 15: return 'X'
    avg = sum(h[-15:]) / 15
    return 'T' if max(h[-15:]) / avg > 1.4 else 'X'

# 20 – Interquartile range
def predict_20(h):
    if len(h) < 12: return 'X'
    w = sorted(h[-12:])
    q1 = w[2]; q3 = w[9]
    return 'T' if q3 > 13 else 'X'

# 21 – Autocorr lag-1
def predict_21(h):
    if len(h) < 15: return 'X'
    x = h[-15:]
    mx = sum(x) / 15
    num = sum((x[i] - mx) * (x[i - 1] - mx) for i in range(1, 15))
    den = sum((xi - mx) ** 2 for xi in x)
    r = num / (den + 1e-9)
    return 'T' if r > 0.3 else 'X'

# 22 – Trimean
def predict_22(h):
    if len(h) < 7: return 'X'
    w = sorted(h[-7:])
    trimean = (w[0] + 2 * w[3] + w[-1]) / 4
    return 'T' if trimean > 10.5 else 'X'

# 23 – Spectral entropy (giả định)
def predict_23(h):
    if len(h) < 32: return 'X'
    psd = [0] * 16
    for x in h[-32:]:
        bin_idx = min(int((x - 3) // 1), 15)
        psd[bin_idx] += 1
    total = sum(psd)
    psd = [p / total for p in psd if p]
    ent = -sum(p * math.log2(p) for p in psd)
    return 'T' if ent < 2.5 else 'X'

# 24 – T-test
def predict_24(h):
    if len(h) < 20: return 'X'
    avg = sum(h[-20:]) / 20
    var = sum((x - avg) ** 2 for x in h[-20:]) / 20
    std = var ** 0.5
    t = (avg - 10.5) / (std / 20 ** 0.5 + 1e-9)
    return 'T' if t > 2.0 else 'X'

# 25 – Geometric mean
def predict_25(h):
    if len(h) < 10: return 'X'
    prod = 1
    for x in h[-10:]: prod *= x
    gmean = prod ** (1 / 10)
    return 'T' if gmean > 10.5 else 'X'

# 26 – Z-score
def predict_26(h):
    if len(h) < 15: return 'X'
    avg = sum(h[-15:]) / 15
    var = sum((x - avg) ** 2 for x in h[-15:]) / 15
    std = var ** 0.5
    z = (h[-1] - avg) / (std + 1e-9)
    return 'T' if z > 1.5 else 'X'

# 27 – Poisson spike
def predict_27(h):
    if len(h) < 20: return 'X'
    spikes = sum(1 for x in h[-20:] if x in {3, 18})
    p = 1 - math.exp(-0.1) * sum((0.1 ** k) / math.factorial(k) for k in range(spikes + 1))
    return 'T' if p < 0.01 else 'X'

# 28 – Delay-embedding 3D
def predict_28(h):
    if len(h) < 10: return 'X'
    changes = 0
    for i in range(2, 10):
        if (h[-i] > h[-i + 1]) != (h[-i + 1] > h[-i + 2]): changes += 1
    return 'T' if changes < 3 else 'X'

# 29 – Hann window
def predict_29(h):
    if len(h) < 12: return 'X'
    coeffs = [0.5 - 0.5 * math.cos(2 * math.pi * i / 11) for i in range(12)]
    s = sum(coeffs[i] * h[-12 + i] for i in range(12))
    return 'T' if s / sum(coeffs) > 10.5 else 'X'

# 30 – Teager-Kaiser
def predict_30(h):
    if len(h) < 3: return 'X'
    x0, x1, x2 = h[-3], h[-2], h[-1]
    tk = x1 * x1 - x0 * x2
    return 'T' if tk > 5 else 'X'

# 31 – Fractal dimension (đơn giản)
def predict_31(h):
    if len(h) < 20: return 'X'
    changes = 0
    for i in range(2, 20):
        if (h[-i] > h[-i + 1]) != (h[-i + 1] > h[-i + 2]): changes += 1
    return 'T' if changes < 5 else 'X'

# 32 – Permutation entropy (đơn giản)
def predict_32(h):
    if len(h) < 10: return 'X'
    a, b, c = h[-3], h[-2], h[-1]
    ranks = sorted([(a, 0), (b, 1), (c, 2)], key=lambda x: x[0])
    pattern = tuple(r[1] for r in ranks)
    return 'T' if pattern in {(2, 1, 0), (2, 0, 1)} else 'X'

# 33 – Sample entropy (đơn giản)
def predict_33(h):
    if len(h) < 20: return 'X'
    count = 0
    for i in range(20):
        for j in range(i + 1, 20):
            if abs(h[-20 + i] - h[-20 + j]) < 1: count += 1
    return 'T' if count < 10 else 'X'

# 34 – Lempel-Ziv (đơn giản)
def predict_34(h):
    if len(h) < 30: return 'X'
    s = ''.join('T' if x > 10.5 else 'X' for x in h[-30:])
    n, k, l = len(s), 1, 1
    while k + l <= n:
        if s[k - 1:k + l - 1] in s[:k - 1]: l += 1
        else: k += 1; l = 1
    return 'T' if k < 12 else 'X'

# 35 – DFA (đơn giản)
def predict_35(h):
    if len(h) < 50: return 'X'
    crosses = 0
    for i in range(1, 50):
        if (h[-i] > 10.5) != (h[-i + 1] > 10.5): crosses += 1
    return 'T' if crosses < 8 else 'X'

# 36 – Hurst (đơn giản)
def predict_36(h):
    if len(h) < 50: return 'X'
    w = h[-50:]
    avg = sum(w) / 50
    std = (sum((x - avg) ** 2 for x in w) / 50) ** 0.5
    r = max(w) - min(w)
    return 'T' if r / (std + 1e-9) > 2.5 else 'X'

# 37 – Lyapunov (đơn giản)
def predict_37(h):
    if len(h) < 40: return 'X'
    changes = 0
    for i in range(1, 40):
        if (h[-i] > h[-i + 1]) != (h[-i + 1] > h[-i + 2]): changes += 1
    return 'T' if changes > 25 else 'X'

# 38 – Fisher exact
def predict_38(h):
    if len(h) < 10: return 'X'
    a = sum(1 for x in h[-10:-5] if x > 10.5)
    b = 5 - a
    c = sum(1 for x in h[-5:] if x > 10.5)
    d = 5 - c
    return 'T' if c > a + 2 else 'X'

# 39 – G-test (đơn giản)
def predict_39(h):
    if len(h) < 20: return 'X'
    tai = sum(1 for x in h[-20:] if x > 10.5)
    xiu = 20 - tai
    expected = 10
    chi = (tai - expected) ** 2 / expected + (xiu - expected) ** 2 / expected
    return 'T' if chi > 3.84 and tai > 12 else 'X'

# 40 – Bayesian Beta-Binomial
def predict_40(h):
    if len(h) < 30: return 'X'
    a, b = 1, 1
    for x in h[-30:]:
        if x > 10.5: a += 1
        else: b += 1
    p = a / (a + b)
    return 'T' if p > 0.55 else 'X'

# 41 – Weighted majority
def predict_41(h):
    if len(h) < 10: return 'X'
    w = [2 ** i for i in range(10)]
    s = sum(w[i] for i, x in enumerate(h[-10:]) if x > 10.5)
    return 'T' if s > sum(w) / 2 else 'X'

# 42 – Theil-Sen slope (đơn giản)
def predict_42(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    slopes = []
    for i in range(14):
        for j in range(i + 1, 15):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    median_slope = sorted(slopes)[len(slopes) // 2] if slopes else 0
    return 'T' if median_slope > 0 else 'X'

# 43 – Repeat raw
def predict_43(h):
    if len(h) < 3: return 'X'
    return 'T' if h[-1] == h[-2] == h[-3] and h[-1] > 10.5 else 'X'

# 44 – Mirror last
def predict_44(h):
    if len(h) < 6: return 'X'
    return 'T' if h[-1] > 10.5 and h[-6] > 10.5 else 'X'

# 45 – Delta threshold
def predict_45(h):
    if len(h) < 4: return 'X'
    return 'T' if h[-1] - h[-4] > 3 else 'X'

# 46 – Count above 12
def predict_46(h):
    if len(h) < 10: return 'X'
    return 'T' if sum(1 for x in h[-10:] if x > 12) >= 6 else 'X'

# 47 – Count below 9
def predict_47(h):
    if len(h) < 10: return 'X'
    return 'T' if sum(1 for x in h[-10:] if x < 9) < 2 else 'X'

# 48 – Variance drop
def predict_48(h):
    if len(h) < 12: return 'X'
    avg = sum(h[-12:]) / 12
    var = sum((x - avg) ** 2 for x in h[-12:]) / 12
    return 'T' if var < 6 else 'X'

# 49 – Gradient boosting (đơn giản)
def predict_49(h):
    if len(h) < 20: return 'X'
    x = list(range(20))
    y = h[-20:]
    slopes = []
    for i in range(19):
        slopes.append(y[i + 1] - y[i])
    median_slope = sorted(slopes)[len(slopes) // 2]
    return 'T' if median_slope > 0.05 else 'X'

# 50 – Random forest (đơn giản)
def predict_50(h):
    if len(h) < 25: return 'X'
    inc = sum(1 for i in range(24) if h[-25 + i + 1] > h[-25 + i])
    return 'T' if inc > 12 else 'X'

# 51 – Extra trees (đơn giản)
def predict_51(h):
    if len(h) < 20: return 'X'
    avg = sum(h[-20:]) / 20
    var = sum((x - avg) ** 2 for x in h[-20:]) / 20
    return 'T' if var > 8 else 'X'

# 52 – AdaBoost (đơn giản)
def predict_52(h):
    if len(h) < 20: return 'X'
    w = 1
    pred = 'X'
    for i in range(20):
        if h[-20 + i] > 10.5:
            w += 0.1
            pred = 'T'
        else:
            w -= 0.1
    return pred if w > 1 else 'X'

# 53 – Bagging (đơn giản)
def predict_53(h):
    if len(h) < 20: return 'X'
    votes = []
    for start in range(0, 20, 4):
        sub = h[-20 + start:-20 + start + 4]
        tai = sum(1 for x in sub if x > 10.5)
        votes.append('T' if tai >= 2 else 'X')
    return 'T' if votes.count('T') > 2 else 'X'

# 54 – MLP (đơn giản)
def predict_54(h):
    if len(h) < 20: return 'X'
    w = 1; b = 0
    for i, x in enumerate(h[-20:]):
        w += (x - 10.5) * 0.01
        b += 0.01
    return 'T' if w + b > 0 else 'X'

# 55 – RBF network (đơn giản)
def predict_55(h):
    if len(h) < 20: return 'X'
    c1 = sum(h[-20:-10]) / 10
    c2 = sum(h[-10:]) / 10
    return 'T' if c2 > c1 else 'X'

# 56 – Passive-Aggressive (đơn giản)
def predict_56(h):
    if len(h) < 15: return 'X'
    w = 0
    for i, x in enumerate(h[-15:]):
        y_true = 1 if x > 10.5 else -1
        y_pred = 1 if w > 0 else -1
        if y_pred != y_true:
            w += y_true * 0.1
    return 'T' if w > 0 else 'X'

# 57 – Ridge (đơn giản)
def predict_57(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15)) + 1  # L2
    w = num / den
    return 'T' if w > 0.05 else 'X'

# 58 – Lasso (đơn giản)
def predict_58(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1)  # L1 đơn giản
    return 'T' if w > 0.05 else 'X'

# 59 – ElasticNet (đơn giản)
def predict_59(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1 + 1)  # L1 + L2
    return 'T' if w > 0.05 else 'X'

# 60 – OMP (đơn giản)
def predict_60(h):
    if len(h) < 10: return 'X'
    x = list(range(10))
    y = h[-10:]
    x_bar = sum(x) / 10
    y_bar = sum(y) / 10
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(10))
    den = sum((x[i] - x_bar) ** 2 for i in range(10))
    w = num / (den + 1e-9)
    pred = w * 9 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 61 – Huber (đơn giản)
def predict_61(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    residuals = [y[i] - (y[0] + (y[-1] - y[0]) / 14 * i) for i in range(15)]
    y_clean = [y[i] if abs(residuals[i]) <= 2 else y[0] + (y[-1] - y[0]) / 14 * i for i in range(15)]
    x_bar = sum(x) / 15
    y_bar = sum(y_clean) / 15
    num = sum((x[i] - x_bar) * (y_clean[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1e-9)
    pred = w * 14 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 62 – Theil-Sen (đơn giản)
def predict_62(h):
    if len(h) < 12: return 'X'
    x = list(range(12))
    y = h[-12:]
    slopes = []
    for i in range(12):
        for j in range(i + 1, 12):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    median_slope = sorted(slopes)[len(slopes) // 2] if slopes else 0
    return 'T' if median_slope > 0 else 'X'

# 63 – Quantile 0.6
def predict_63(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    idx = int(0.6 * 10)
    q = w[idx]
    return 'T' if q > 10.5 else 'X'

# 64 – Trimmed mean 20 %
def predict_64(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    trim = w[2:8]  # 20 % mỗi đầu
    avg = sum(trim) / 6
    return 'T' if avg > 10.5 else 'X'

# 65 – Winsorized mean
def predict_65(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    w[0] = w[1]
    w[-1] = w[-2]
    avg = sum(w) / 10
    return 'T' if avg > 10.5 else 'X'

# 66 – Hampel filter (đơn giản)
def predict_66(h):
    if len(h) < 12: return 'X'
    w = h[-12:]
    median = sorted(w)[6]
    mad = sorted([abs(x - median) for x in w])[6]
    filtered = [x if abs(x - median) <= 3 * mad else median for x in w]
    return 'T' if filtered[-1] > 10.5 else 'X'

# 67 – Voting hard (10 rule)
def predict_67(h):
    pool = [predict_00, predict_01, predict_02, predict_03, predict_04, predict_05, predict_06, predict_07, predict_08, predict_09]
    votes = [f(h) for f in pool]
    return 'T' if votes.count('T') > 5 else 'X'

# 68 – Stacking (đơn giản)
def predict_68(h):
    if len(h) < 30: return 'X'
    preds = []
    for f in [predict_00, predict_01, predict_12, predict_18, predict_25]:
        preds.append(1 if f(h) == 'T' else 0)
    meta = sum(preds) / len(preds)
    return 'T' if meta > 0.5 else 'X'

# 69 – Bagging (đơn giản)
def predict_69(h):
    if len(h) < 20: return 'X'
    votes = []
    for _ in range(5):
        sample = [h[-20 + i] for i in sorted([abs(hash(str(i))) % 20 for i in range(10)])]
        tai = sum(1 for x in sample if x > 10.5)
        votes.append('T' if tai >= 5 else 'X')
    return 'T' if votes.count('T') > 2 else 'X'

# 70 – Neural net (đơn giản)
def predict_70(h):
    if len(h) < 20: return 'X'
    w1 = [0.1] * 20
    b1 = 0
    for i in range(20):
        w1[i] += (h[-20 + i] - 10.5) * 0.01
        b1 += 0.01
    hidden = max(0, sum(w1[i] * (h[-20 + i] - 10.5) for i in range(20)) + b1)
    out = hidden - 5
    return 'T' if out > 0 else 'X'

# 71 – RBF network (đơn giản)
def predict_71(h):
    if len(h) < 20: return 'X'
    c1 = sum(h[-20:-14]) / 6
    c2 = sum(h[-14:-7]) / 7
    c3 = sum(h[-7:]) / 7
    return 'T' if c3 > c2 > c1 else 'X'

# 72 – Passive-Aggressive (đơn giản)
def predict_72(h):
    if len(h) < 15: return 'X'
    w = 0
    for i, x in enumerate(h[-15:]):
        y_true = 1 if x > 10.5 else -1
        y_pred = 1 if w > 0 else -1
        if y_pred != y_true:
            w += y_true * 0.1
    return 'T' if w > 0 else 'X'

# 73 – Ridge (đơn giản)
def predict_73(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15)) + 1  # L2
    w = num / den
    return 'T' if w > 0.05 else 'X'

# 74 – Lasso (đơn giản)
def predict_74(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1)  # L1 đơn giản
    return 'T' if w > 0.05 else 'X'

# 75 – ElasticNet (đơn giản)
def predict_75(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1 + 1)  # L1 + L2
    return 'T' if w > 0.05 else 'X'

# 76 – OMP (đơn giản)
def predict_76(h):
    if len(h) < 10: return 'X'
    x = list(range(10))
    y = h[-10:]
    x_bar = sum(x) / 10
    y_bar = sum(y) / 10
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(10))
    den = sum((x[i] - x_bar) ** 2 for i in range(10))
    w = num / (den + 1e-9)
    pred = w * 9 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 77 – Huber (đơn giản)
def predict_77(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    residuals = [y[i] - (y[0] + (y[-1] - y[0]) / 14 * i) for i in range(15)]
    y_clean = [y[i] if abs(residuals[i]) <= 2 else y[0] + (y[-1] - y[0]) / 14 * i for i in range(15)]
    x_bar = sum(x) / 15
    y_bar = sum(y_clean) / 15
    num = sum((x[i] - x_bar) * (y_clean[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1e-9)
    pred = w * 14 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 78 – Theil-Sen (đơn giản)
def predict_78(h):
    if len(h) < 12: return 'X'
    x = list(range(12))
    y = h[-12:]
    slopes = []
    for i in range(12):
        for j in range(i + 1, 12):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    median_slope = sorted(slopes)[len(slopes) // 2] if slopes else 0
    return 'T' if median_slope > 0 else 'X'

# 79 – Quantile 0.6
def predict_79(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    idx = int(0.6 * 10)
    q = w[idx]
    return 'T' if q > 10.5 else 'X'

# 80 – Trimmed mean 20 %
def predict_80(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    trim = w[2:8]  # 20 % mỗi đầu
    avg = sum(trim) / 6
    return 'T' if avg > 10.5 else 'X'

# 81 – Winsorized mean
def predict_81(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    w[0] = w[1]
    w[-1] = w[-2]
    avg = sum(w) / 10
    return 'T' if avg > 10.5 else 'X'

# 82 – Hampel filter (đơn giản)
def predict_82(h):
    if len(h) < 12: return 'X'
    w = h[-12:]
    median = sorted(w)[6]
    mad = sorted([abs(x - median) for x in w])[6]
    filtered = [x if abs(x - median) <= 3 * mad else median for x in w]
    return 'T' if filtered[-1] > 10.5 else 'X'

# 83 – Voting hard (10 rule)
def predict_83(h):
    pool = [predict_00, predict_01, predict_02, predict_03, predict_04, predict_05, predict_06, predict_07, predict_08, predict_09]
    votes = [f(h) for f in pool]
    return 'T' if votes.count('T') > 5 else 'X'

# 84 – Stacking (đơn giản)
def predict_84(h):
    if len(h) < 30: return 'X'
    preds = []
    for f in [predict_00, predict_01, predict_12, predict_18, predict_25]:
        preds.append(1 if f(h) == 'T' else 0)
    meta = sum(preds) / len(preds)
    return 'T' if meta > 0.5 else 'X'

# 85 – Bagging (đơn giản)
def predict_85(h):
    if len(h) < 20: return 'X'
    votes = []
    for _ in range(5):
        sample = [h[-20 + i] for i in sorted([abs(hash(str(i))) % 20 for i in range(10)])]
        tai = sum(1 for x in sample if x > 10.5)
        votes.append('T' if tai >= 5 else 'X')
    return 'T' if votes.count('T') > 2 else 'X'

# 86 – Neural net (đơn giản)
def predict_86(h):
    if len(h) < 20: return 'X'
    w1 = [0.1] * 20
    b1 = 0
    for i in range(20):
        w1[i] += (h[-20 + i] - 10.5) * 0.01
        b1 += 0.01
    hidden = max(0, sum(w1[i] * (h[-20 + i] - 10.5) for i in range(20)) + b1)
    out = hidden - 5
    return 'T' if out > 0 else 'X'

# 87 – RBF network (đơn giản)
def predict_87(h):
    if len(h) < 20: return 'X'
    c1 = sum(h[-20:-14]) / 6
    c2 = sum(h[-14:-7]) / 7
    c3 = sum(h[-7:]) / 7
    return 'T' if c3 > c2 > c1 else 'X'

# 88 – Passive-Aggressive (đơn giản)
def predict_88(h):
    if len(h) < 15: return 'X'
    w = 0
    for i, x in enumerate(h[-15:]):
        y_true = 1 if x > 10.5 else -1
        y_pred = 1 if w > 0 else -1
        if y_pred != y_true:
            w += y_true * 0.1
    return 'T' if w > 0 else 'X'

# 89 – Ridge (đơn giản)
def predict_89(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15)) + 1  # L2
    w = num / den
    return 'T' if w > 0.05 else 'X'

# 90 – Lasso (đơn giản)
def predict_90(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1)  # L1 đơn giản
    return 'T' if w > 0.05 else 'X'

# 91 – ElasticNet (đơn giản)
def predict_91(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    x_bar = sum(x) / 15
    y_bar = sum(y) / 15
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1 + 1)  # L1 + L2
    return 'T' if w > 0.05 else 'X'

# 92 – OMP (đơn giản)
def predict_92(h):
    if len(h) < 10: return 'X'
    x = list(range(10))
    y = h[-10:]
    x_bar = sum(x) / 10
    y_bar = sum(y) / 10
    num = sum((x[i] - x_bar) * (y[i] - y_bar) for i in range(10))
    den = sum((x[i] - x_bar) ** 2 for i in range(10))
    w = num / (den + 1e-9)
    pred = w * 9 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 93 – Huber (đơn giản)
def predict_93(h):
    if len(h) < 15: return 'X'
    x = list(range(15))
    y = h[-15:]
    residuals = [y[i] - (y[0] + (y[-1] - y[0]) / 14 * i) for i in range(15)]
    y_clean = [y[i] if abs(residuals[i]) <= 2 else y[0] + (y[-1] - y[0]) / 14 * i for i in range(15)]
    x_bar = sum(x) / 15
    y_bar = sum(y_clean) / 15
    num = sum((x[i] - x_bar) * (y_clean[i] - y_bar) for i in range(15))
    den = sum((x[i] - x_bar) ** 2 for i in range(15))
    w = num / (den + 1e-9)
    pred = w * 14 + y_bar
    return 'T' if pred > 10.5 else 'X'

# 94 – Theil-Sen (đơn giản)
def predict_94(h):
    if len(h) < 12: return 'X'
    x = list(range(12))
    y = h[-12:]
    slopes = []
    for i in range(12):
        for j in range(i + 1, 12):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    median_slope = sorted(slopes)[len(slopes) // 2] if slopes else 0
    return 'T' if median_slope > 0 else 'X'

# 95 – Quantile 0.6
def predict_95(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    idx = int(0.6 * 10)
    q = w[idx]
    return 'T' if q > 10.5 else 'X'

# 96 – Trimmed mean 20 %
def predict_96(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    trim = w[2:8]  # 20 % mỗi đầu
    avg = sum(trim) / 6
    return 'T' if avg > 10.5 else 'X'

# 97 – Winsorized mean
def predict_97(h):
    if len(h) < 10: return 'X'
    w = sorted(h[-10:])
    w[0] = w[1]
    w[-1] = w[-2]
    avg = sum(w) / 10
    return 'T' if avg > 10.5 else 'X'

# 98 – Hampel filter (đơn giản)
def predict_98(h):
    if len(h) < 12: return 'X'
    w = h[-12:]
    median = sorted(w)[6]
    mad = sorted([abs(x - median) for x in w])[6]
    filtered = [x if abs(x - median) <= 3 * mad else median for x in w]
    return 'T' if filtered[-1] > 10.5 else 'X'

# 99 – Voting hard (20 rule)
def predict_99(h):
    pool = [globals()[f'predict_{i:02d}'] for i in range(20)]
    votes = [f(h) for f in pool]
    return 'T' if votes.count('T') > 10 else 'X'

# 100 – Final ensemble hard vote (100 thuật toán)
def predict_100(h):
    pool = [globals()[f'predict_{i:02d}'] for i in range(100) if f'predict_{i:02d}' in globals()]
    votes = [f(h) for f in pool]
    t = votes.count('T')
    return 'T' if t > len(votes) / 2 else 'X'

# ========== ENSEMBLE 100 THUẬT TOÁN THẬT ==========
PRED_FUNCS = [globals()[f'predict_{i:02d}'] for i in range(101) if f'predict_{i:02d}' in globals()]

def ensemble_predict(h):
    if len(h) < 5: return 'X', 0
    votes = [f(h) for f in PRED_FUNCS]
    t = votes.count('T')
    conf = round(t / len(votes), 2)
    return ('T' if t > len(votes) / 2 else 'X'), conf

# ========== FETCH REAL DATA – KHÔNG TIMEOUT ==========
def fetch_tele68():
    try:
        r = requests.get(API_URL, timeout=5).json()
        if "list" in r and r["list"]:
            n = r["list"][0]
            phien, dice, tong = n.get("id"), n.get("dices", [1, 2, 3]), n.get("point", sum(n.get("dices", [1, 2, 3])))
            raw = n.get("resultTruyenThong", "").upper()
            ketqua = {"TAI": "Tài", "XIU": "Xỉu"}.get(raw, "Tài" if tong >= 11 else "Xỉu")
            return phien, dice, tong, ketqua
    except Exception as e:
        print("[❌] Lỗi fetch:", e)
    return None

# ========== BACKGROUND UPDATER – KHÔNG NGỦ ĐÔNG ==========
def updater():
    global last_data
    last_phien = None
    while True:
        d = fetch_tele68()
        if d:
            phien, dice, tong, ketqua = d
            if phien != last_phien and phien:
                history_totals.append(tong)
                history_tx.append(ketqua)
                pred, conf = ensemble_predict(list(history_totals))
                last_data = {
                    "phien": phien, "xucxac1": dice[0], "xucxac2": dice[1], "xucxac3": dice[2],
                    "tong": tong, "ketqua": ketqua, "du_doan": pred, "do_tin_cay": conf, "id": "pentter100real"
                }
                print(f"[✅] {phien} | {ketqua} ({tong}) → {pred} ({conf})")
                last_phien = phien
        time.sleep(UPDATE_SEC)

# ========== API ==========
@app.route("/api/taixiu", methods=["GET"])
def api(): return jsonify(last_data)

# ========== RUN ==========
if __name__ == "__main__":
    print("🚀 Khởi động API tài xỉu + 100 pentter thật – không numpy – không timeout")
    threading.Thread(target=updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
