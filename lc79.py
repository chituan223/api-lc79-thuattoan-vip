# app.py – Full tài xỉu Tele68 + 100 pentter thật
from flask import Flask, jsonify
import requests, time, threading, os, math, numpy as np
from collections import deque

app = Flask(__name__)

# ==================== CONFIG ====================
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
UPDATE_SEC = 5
HISTORY_MAX = 1000
# ================================================

history_totals = deque(maxlen=HISTORY_MAX)   # lưu tổng 3 xúc xắc
history_tx     = deque(maxlen=HISTORY_MAX)   # lưu 'T'|'X'

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Chờ dữ liệu...",
    "do_tin_cay": 0,
    "id": "pentter99"
}

# ==================== 100 PENTTER ====================
# -------------- import nhẹ --------------
from scipy.stats import chisquare, ttest_1samp, poisson, fisher_exact, power_divergence, theilslopes
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier, Lasso, ElasticNet, OrthogonalMatchingPursuit, HuberRegressor, TheilSenRegressor, PassiveAggressiveClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest, RandomForestClassifier, ExtraTreesClassifier, AdaBoostClassifier, GradientBoostingClassifier, StackingClassifier, BaggingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.kernel_approximation import RBFSampler
from sklearn.linear_model import SGDClassifier
from sklearn.tree import DecisionTreeClassifier
import pywt, nolds, antropy, hampel
from mne.time_frequency import permutation_entropy
from statsmodels.tsa.filters.hp_filter import hpfilter
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.arima.model import ARIMA
# ---------------------------------------

# 0
def predict_00(h):
    if len(h) < 10: return 'X'
    return 'T' if (sum(h[-10:])/10) < 10.5 else 'X'

# 1
def predict_01(h):
    if len(h) < 5: return 'X'
    last = h[-5:]
    if all(x > 10.5 for x in last): return 'X'
    if all(x < 10.5 for x in last): return 'T'
    return 'X'

# 2
def entropy(w):
    c = [0]*19
    for x in w: c[x] += 1
    return -sum(p/len(w)*math.log2(p/len(w)) for p in c if p)
def predict_02(h):
    if len(h) < 20: return 'X'
    return 'T' if entropy(h[-20:]) < 2.8 else 'X'

# 3
def predict_03(h):
    if len(h) < 32: return 'X'
    fft = np.fft.rfft([x-10.5 for x in h[-32:]])
    dom = np.argmax(np.abs(fft[1:13]))+1
    return 'T' if dom < 6 else 'X'

# 4
def predict_04(h):
    if len(h) < 3: return 'X'
    trans = {'TT':0,'TX':0,'XT':0,'XX':0}
    for i in range(1,len(h)):
        k = ('T' if h[i-1]>10.5 else 'X') + ('T' if h[i]>10.5 else 'X')
        trans[k] += 1
    last = ('T' if h[-2]>10.5 else 'X') + ('T' if h[-1]>10.5 else 'X')
    return 'T' if trans[last+'T'] > trans[last+'X'] else 'X'

# 5
def predict_05(h):
    if len(h) < 50: return 'X'
    o = [sum(1 for x in h[-50:] if x == i) for i in range(3,19)]
    _, p = chisquare(o)
    return 'T' if p < 0.05 and np.mean(h[-50:]) > 10.5 else 'X'

# 6
def predict_06(h):
    if not h: return 'X'
    alpha = 0.25
    s = h[0]
    for x in h[1:]: s = alpha*x + (1-alpha)*s
    return 'T' if s > 10.5 else 'X'

# 7
def predict_07(h):
    gaps = [i for i,x in enumerate(h[-20:],1) if 10 <= x <= 11]
    return 'T' if len(gaps) < 4 else 'X'

# 8
def predict_08(h):
    if len(h) < 30: return 'X'
    r, cnt = 1, 1
    for i in range(1,30):
        if (h[-i]>10.5) != (h[-i-1]>10.5): r += 1; cnt += 1
        else: cnt += 1
    return 'T' if r < cnt/3 else 'X'

# 9
def predict_09(h):
    if len(h) < 15: return 'X'
    w = h[-15:]
    return 'T' if (max(w)-min(w)) < 5 else 'X'

# 10
def predict_10(h):
    c = sum(1 for x in h[-20:] if x in {3,18})
    p = 1-poisson(20*0.005).cdf(c)
    return 'T' if p < 0.01 else 'X'

# 11
def predict_11(h):
    if len(h) < 10: return 'X'
    emb = np.array([[h[i],h[i-1],h[i-2]] for i in range(-1,-8,-1)])
    cov = np.cov(emb, rowvar=False)
    return 'T' if np.linalg.det(cov) < 20 else 'X'

# 12
def predict_12(h):
    if len(h) < 7: return 'X'
    return 'T' if sum(x>10.5 for x in h[-7:]) >= 4 else 'X'

# 13
def predict_13(h):
    if len(h) < 12: return 'X'
    return 'T' if max(h[-12:])-min(h[-12:]) > 12 else 'X'

# 14
def predict_14(h):
    if len(h) < 9: return 'X'
    m = sorted(h[-9:])[4]
    return 'T' if m > 10.5 else 'X'

# 15
def predict_15(h):
    if len(h) < 25: return 'X'
    s = 0
    for x in h[-25:]:
        s += x - 10.5
        if abs(s) > 25: return 'T' if s > 0 else 'X'
    return 'X'

# 16
def predict_16(h):
    if len(h) < 23: return 'X'
    return 'T' if len(set(h[-23:])) < 16 else 'X'

# 17
def predict_17(h):
    if len(h) < 15: return 'X'
    w = h[-15:]
    z = (w[-1] - np.mean(w))/np.std(w)
    return 'T' if z > 1.5 else 'X'

# 18
def predict_18(h):
    if len(h) < 20: return 'X'
    x = np.arange(20)
    y = h[-20:]
    m, _ = np.polyfit(x,y,1)
    return 'T' if m > 0.1 else 'X'

# 19
def predict_19(h):
    from statistics import mode
    if len(h) < 12: return 'X'
    try: m = mode(h[-12:])
    except: return 'X'
    return 'T' if m > 10.5 else 'X'

# 20
def predict_20(h):
    wins = sum(1 for x in h[-50:] if x > 10.5)
    p = wins/50 if len(h)>=50 else 0.5
    return 'T' if p > 0.52 else 'X'

# 21
def predict_21(h):
    if len(h) < 14: return 'X'
    gains = [x-10.5 for x in h[-14:] if x>10.5]
    losses = [10.5-x for x in h[-14:] if x<=10.5]
    rs = (sum(gains)/14)/(sum(losses)/14+0.001)
    return 'T' if rs > 1.2 else 'X'

# 22
def predict_22(h):
    if len(h) < 20: return 'X'
    m = np.mean(h[-20:])
    s = np.std(h[-20:])
    return 'T' if h[-1] > m+1.5*s else 'X'

# 23
def predict_23(h):
    if len(h) < 40: return 'X'
    pos = sum(1 for x in h[-40:] if x > 10.5)
    return 'T' if pos < 8 or pos > 32 else 'X'

# 24
def predict_24(h):
    if len(h) < 30: return 'X'
    first = [int(str(x)[0]) for x in h[-30:]]
    return 'T' if first.count(1) < 3 else 'X'

# 25
def predict_25(h):
    if len(h) < 10: return 'X'
    pat = ''.join(['T' if x>10.5 else 'X' for x in h[-10:]])
    for k,v in {'T'*5:'X','X'*5:'T'}.items():
        if k in pat: return v
    return 'X'

# 26
def predict_26(h):
    if len(h) < 15: return 'X'
    return 'T' if max(h[-15:])/(np.mean(h[-15:])) > 1.4 else 'X'

# 27
def predict_27(h):
    if len(h) < 25: return 'X'
    tails = sum(1 for x in h[-25:] if x in {3,4,5,16,17,18})
    return 'T' if tails > 6 else 'X'

# 28
def predict_28(h):
    if len(h) < 5: return 'X'
    d = [h[i]-h[i-1] for i in range(-1,-5,-1)]
    return 'T' if all(x>0 for x in d) else 'X'

# 29
def predict_29(h):
    from collections import Counter
    if len(h) < 20: return 'X'
    c = Counter(h[-20:])
    pmax = max(c.values())/20
    return 'T' if -math.log2(pmax+1e-12) < 3 else 'X'

# 30
def predict_30(h):
    if len(h) < 30: return 'X'
    g = GaussianMixture(n_components=2).fit(np.array(h[-30:]).reshape(-1,1))
    return 'T' if np.argmax(g.means_.flatten()) == 1 else 'X'

# 31
def predict_31(h):
    if len(h) < 20: return 'X'
    return 'T' if np.mean(h[-10:]) - np.mean(h[-20:-10]) > 1.5 else 'X'

# 32
def predict_32(h):
    if len(h) < 30: return 'X'
    m, M = 0, 0
    for x in h[-30:]:
        m += x - 10.5
        if m < M: M = m
    return 'T' if m - M > 15 else 'X'

# 33
def predict_33(h):
    if len(h) < 7: return 'X'
    w = sorted(h[-7:])
    trimean = (w[0] + 2*w[3] + w[-1])/4
    return 'T' if trimean > 10.5 else 'X'

# 34
def predict_34(h):
    if len(h) < 32: return 'X'
    psd = np.abs(np.fft.rfft([x-10.5 for x in h[-32:]]))**2
    psd /= psd.sum()
    return 'T' if -sum(p*math.log2(p+1e-12) for p in psd) < 2.5 else 'X'

# 35
def predict_35(h):
    if len(h) < 20: return 'X'
    _, p = ttest_1samp(h[-20:], 10.5)
    return 'T' if p < 0.05 and np.mean(h[-20:]) > 10.5 else 'X'

# 36
def predict_36(h):
    if len(h) < 10: return 'X'
    from scipy.stats import gmean
    return 'T' if gmean(h[-10:]) > 10.5 else 'X'

# 37
def predict_37(h):
    if len(h) < 15: return 'X'
    x = h[-15:]
    c = np.corrcoef(x[:-1], x[1:])[0,1]
    return 'T' if c > 0.3 else 'X'

# 38
def predict_38(h):
    if len(h) < 12: return 'X'
    q3 = np.percentile(h[-12:], 75)
    return 'T' if q3 > 13 else 'X'

# 39
def predict_39(h):
    if len(h) < 30: return 'X'
    X = np.arange(30).reshape(-1,1)
    y = (np.array(h[-30:]) > 10.5).astype(int)
    return 'T' if SVC(kernel='linear', C=1).fit(X,y).predict([[29.5]])[0] else 'X'

# 40
def predict_40(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if KNeighborsClassifier(n_neighbors=5).fit(X,y).predict([[19.5]])[0] else 'X'

# 41
def predict_41(h):
    if len(h) < 15: return 'X'
    return 'T' if h[-1] > np.median(h[-15:]) else 'X'

# 42
def predict_42(h):
    if len(h) < 25: return 'X'
    X = np.arange(25).reshape(-1,1)
    y = (np.array(h[-25:]) > 10.5).astype(int)
    return 'T' if LogisticRegression().fit(X,y).predict([[24.5]])[0] else 'X'

# 43
def predict_43(h):
    if len(h) < 20: return 'X'
    X = np.array(h[-20:]).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if GaussianNB().fit(X,y).predict([[h[-1]]])[0] else 'X'

# 44
def predict_44(h):
    if len(h) < 30: return 'X'
    X = np.array(h[-30:]).reshape(-1,1)
    lbl = DBSCAN(eps=2, min_samples=3).fit_predict(X)
    return 'T' if lbl[-1] == -1 else 'X'

# 45
def predict_45(h):
    if len(h) < 30: return 'X'
    X = np.array(h[-30:]).reshape(-1,1)
    return 'T' if IsolationForest().fit_predict(X)[-1] == -1 else 'X'

# 46
def predict_46(h):
    if len(h) < 15: return 'X'
    from scipy.stats import skew
    return 'T' if skew(h[-15:]) > 0.5 else 'X'

# 47
def predict_47(h):
    if len(h) < 15: return 'X'
    from scipy.stats import kurtosis
    return 'T' if kurtosis(h[-15:]) > 1 else 'X'

# 48
def predict_48(h):
    if len(h) < 10: return 'X'
    x = np.arange(10)
    y = np.array(h[-10:])
    grad = np.gradient(y, x)
    return 'T' if np.gradient(grad, x)[-1] < 0 else 'X'

# 49
def predict_49(h):
    if len(h) < 11: return 'X'
    smooth = savgol_filter(h[-11:], 5, 2)
    return 'T' if smooth[-1] > 10.5 else 'X'

# 50
def predict_50(h):
    if len(h) < 20: return 'X'
    _, trend = hpfilter(h[-20:], 1600)
    return 'T' if trend[-1] > 10.5 else 'X'

# 51
def predict_51(h):
    if len(h) < 24: return 'X'
    res = STL(h[-24:], period=6).fit()
    return 'T' if res.trend[-1] > 10.5 else 'X'

# 52
def predict_52(h):
    if len(h) < 30: return 'X'
    try:
        model = ARIMA(h[-30:], order=(1,0,1)).fit()
        f = model.forecast()[0]
    except: return 'X'
    return 'T' if f > 10.5 else 'X'

# 53
def predict_53(h):
    if len(h) < 20: return 'X'
    x = np.arange(20)
    y = h[-20:]
    m, b = np.polyfit(x,y,1)
    return 'T' if m*20+b > 10.5 else 'X'

# 54
def predict_54(h):
    if len(h) < 16: return 'X'
    coef, _ = pywt.dwt([x-10.5 for x in h[-16:]], 'db2')
    return 'T' if max(coef) > 3 else 'X'

# 55
def predict_55(h):
    if len(h) < 12: return 'X'
    w = np.hanning(12)
    return 'T' if np.dot(w, h[-12:])/w.sum() > 10.5 else 'X'

# 56
def predict_56(h):
    if len(h) < 5: return 'X'
    x = h[-3:]
    tk = x[1]**2 - x[0]*x[2]
    return 'T' if tk > 5 else 'X'

# 57
def predict_57(h):
    if len(h) < 20: return 'X'
    x = h[-20:]
    lengths = []
    for k in [2,4,5,10]:
        L = sum(abs(x[i]-x[i-k]) for i in range(k,20,k))
        lengths.append(L)
    return 'T' if np.std(lengths) < 5 else 'X'

# 58
def predict_58(h):
    if len(h) < 10: return 'X'
    return 'T' if permutation_entropy(h[-10:], order=3, delay=1) < 0.5 else 'X'

# 59
def predict_59(h):
    if len(h) < 20: return 'X'
    return 'T' if antropy.sample_entropy(h[-20:]) < 0.8 else 'X'

# 60
def predict_60(h):
    if len(h) < 30: return 'X'
    s = ''.join('T' if x>10.5 else 'X' for x in h[-30:])
    n, k, l = len(s), 1, 1
    while k+l <= n:
        if s[k-1:k+l-1] in s[:k-1]: l += 1
        else: k += 1; l = 1
    return 'T' if k < 12 else 'X'

# 61
def predict_61(h):
    if len(h) < 50: return 'X'
    return 'T' if nolds.dfa(h[-50:]) < 1.2 else 'X'

# 62
def predict_62(h):
    if len(h) < 50: return 'X'
    return 'T' if nolds.hurst_rs(h[-50:]) > 0.6 else 'X'

# 63
def predict_63(h):
    if len(h) < 40: return 'X'
    return 'T' if nolds.lyap_r(h[-40:]) > 0.01 else 'X'

# 64
def predict_64(h):
    if len(h) < 9: return 'X'
    last3 = h[-3:]
    ranks = tuple(sorted(range(3), key=lambda i: last3[i]))
    return 'T' if ranks in [(2,1,0),(2,0,1)] else 'X'

# 65
def predict_65(h):
    if len(h) < 30: return 'X'
    s = sum((x - 10.5)**2 for x in h[-30:])
    return 'T' if s > 300 else 'X'

# 66
def predict_66(h):
    if len(h) < 10: return 'X'
    a = sum(1 for x in h[-10:-5] if x > 10.5)
    b = 5-a
    c = sum(1 for x in h[-5:] if x > 10.5)
    d = 5-c
    _, p = fisher_exact([[a,b],[c,d]])
    return 'T' if p < 0.1 and c > 3 else 'X'

# 67
def predict_67(h):
    if len(h) < 20: return 'X'
    obs = [sum(1 for x in h[-20:] if x > 10.5), sum(1 for x in h[-20:] if x <= 10.5)]
    _, p = power_divergence(obs)
    return 'T' if p < 0.05 and obs[0] > 12 else 'X'

# 68
def predict_68(h):
    if len(h) < 30: return 'X'
    a, b = 1, 1
    for x in h[-30:]:
        if x > 10.5: a += 1
        else: b += 1
    p = a/(a+b)
    return 'T' if p > 0.55 else 'X'

# 69  (cần random nhẹ)
def predict_69(h):
    if len(h) < 20: return 'X'
    a = 1 + sum(1 for x in h[-20:] if x > 10.5)
    b = 1 + sum(1 for x in h[-20:] if x <= 10.5)
    sample = np.random.beta(a, b)
    return 'T' if sample > 0.5 else 'X'

# 70
def predict_70(h):
    if len(h) < 10: return 'X'
    w = [2**i for i in range(10)]
    s = sum(w[i] for i,x in enumerate(h[-10:]) if x > 10.5)
    return 'T' if s > sum(w)/2 else 'X'

# 71
def predict_71(h):
    if not h: return 'X'
    s1, s2 = h[0], h[0]
    for x in h[1:]:
        s1 = 0.3*x + 0.7*s1
        s2 = 0.3*s1 + 0.7*s2
    return 'T' if s2 > 10.5 else 'X'

# 72
def predict_72(h):
    if len(h) < 15: return 'X'
    x = np.arange(15)
    y = h[-15:]
    slope, _, _, _ = theilslopes(y, x)
    return 'T' if slope > 0 else 'X'

# 73
def predict_73(h):
    if len(h) < 3: return 'X'
    return 'T' if h[-1]==h[-2]==h[-3] and h[-1]>10.5 else 'X'

# 74
def predict_74(h):
    if len(h) < 6: return 'X'
    return 'T' if h[-1] > 10.5 and h[-6] > 10.5 else 'X'

# 75
def predict_75(h):
    if len(h) < 4: return 'X'
    return 'T' if h[-1] - h[-4] > 3 else 'X'

# 76
def predict_76(h):
    if len(h) < 10: return 'X'
    return 'T' if sum(x>12 for x in h[-10:]) >= 6 else 'X'

# 77
def predict_77(h):
    if len(h) < 10: return 'X'
    return 'T' if sum(x<9 for x in h[-10:]) < 2 else 'X'

# 78
def predict_78(h):
    if len(h) < 12: return 'X'
    return 'T' if np.var(h[-12:]) < 6 else 'X'

# 79
def predict_79(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if GradientBoostingClassifier().fit(X,y).predict([[19.5]])[0] else 'X'

# 80
def predict_80(h):
    if len(h) < 25: return 'X'
    X = np.arange(25).reshape(-1,1)
    y = (np.array(h[-25:]) > 10.5).astype(int)
    return 'T' if RandomForestClassifier(n_estimators=30).fit(X,y).predict([[24.5]])[0] else 'X'

# 81
def predict_81(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if ExtraTreesClassifier().fit(X,y).predict([[19.5]])[0] else 'X'

# 82
def predict_82(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if AdaBoostClassifier().fit(X,y).predict([[19.5]])[0] else 'X'

# 83  (vote 3 mẫu đầu)
def predict_83(h):
    votes = [predict_00(h), predict_01(h), predict_02(h)]
    return 'T' if votes.count('T') > len(votes)/2 else 'X'

# 84
def predict_84(h):
    if len(h) < 30: return 'X'
    estimators = [('dt', DecisionTreeClassifier()), ('lr', LogisticRegression())]
    X = np.arange(30).reshape(-1,1)
    y = (np.array(h[-30:]) > 10.5).astype(int)
    return 'T' if StackingClassifier(estimators, final_estimator=LogisticRegression()).fit(X,y).predict([[29.5]])[0] else 'X'

# 85
def predict_85(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if BaggingClassifier(DecisionTreeClassifier()).fit(X,y).predict([[19.5]])[0] else 'X'

# 86
def predict_86(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    return 'T' if MLPClassifier(hidden_layer_sizes=(10,), max_iter=500).fit(X,y).predict([[19.5]])[0] else 'X'

# 87
def predict_87(h):
    if len(h) < 20: return 'X'
    X = np.arange(20).reshape(-1,1)
    y = (np.array(h[-20:]) > 10.5).astype(int)
    rbf = RBFSampler(gamma=0.5, random_state=1).fit_transform(X)
    return 'T' if SGDClassifier().fit(rbf,y).predict(rbf[-1].reshape(1,-1))[0] else 'X'

# 88
def predict_88(h):
    if len(h) < 15: return 'X'
    X = np.arange(15).reshape(-1,1)
    y = (np.array(h[-15:]) > 10.5).astype(int)
    return 'T' if PassiveAggressiveClassifier().fit(X,y).predict([[14.5]])[0] else 'X'

# 89
def predict_89(h):
    if len(h) < 15: return 'X'
    X = np.arange(15).reshape(-1,1)
    y = (np.array(h[-15:]) > 10.5).astype(int)
    return 'T' if RidgeClassifier().fit(X,y).predict([[14.5]])[0] else 'X'

# 90
def predict_90(h):
    if len(h) < 15: return 'X'
    X = np.arange(15).reshape(-1,1)
    y = np.array(h[-15:])
    coef = Lasso(alpha=0.1).fit(X,y).coef_[0]
    return 'T' if coef > 0.05 else 'X'

# 91
def predict_91(h):
    if len(h) < 15: return 'X'
    X = np.arange(15).reshape(-1,1)
    y = np.array(h[-15:])
    coef = ElasticNet(alpha=0.1, l1_ratio=0.5).fit(X,y).coef_[0]
    return 'T' if coef > 0.05 else 'X'

# 92
def predict_92(h):
    if len(h) < 10: return 'X'
    X = np.arange(10).reshape(-1,1)
    y = np.array(h[-10:])
    return 'T' if OrthogonalMatchingPursuit().fit(X,y).predict([[9.5]])[0] > 10.5 else 'X'

# 93
def predict_93(h):
    if len(h) < 15: return 'X'
    X = np.arange(15).reshape(-1,1)
    y = np.array(h[-15:])
    return 'T' if HuberRegressor().fit(X,y).predict([[14.5]])[0] > 10.5 else 'X'

# 94
def predict_94(h):
    if len(h) < 12: return 'X'
    X = np.arange(12).reshape(-1,1)
    y = np.array(h[-12:])
    return 'T' if TheilSenRegressor().fit(X,y).predict([[11.5]])[0] > 10.5 else 'X'

# 95
def predict_95(h):
    if len(h) < 10: return 'X'
    return 'T' if np.quantile(h[-10:], 0.6) > 10.5 else 'X'

# 96
def predict_96(h):
    if len(h) < 10: return 'X'
    from scipy.stats import trim_mean
    return 'T' if trim_mean(h[-10:], 0.2) > 10.5 else 'X'

# 97
def predict_97(h):
    if len(h) < 10: return 'X'
    from scipy.stats import mstats
    return 'T' if mstats.winsorize(h[-10:], limits=[0.1,0.1]).mean() > 10.5 else 'X'

# 98
def predict_98(h):
    if len(h) < 12: return 'X'
    return 'T' if hampel.hampel(h[-12:]).filtered_data[-1] > 10.5 else 'X'

# 99  (ensemble 5 mẫu)
def predict_99(h):
    pool = [predict_00, predict_01, predict_02, predict_03, predict_04]
    votes = [f(h) for f in pool]
    return 'T' if votes.count('T') >= 3 else 'X'

# ==================== GIỌI HẠN 100 THUẬT TOÁN ====================

PREDICTORS = [globals()[f'predict_{i:02d}'] for i in range(100)]

def ensemble_predict(h):
    if len(h) < 5: return 'X', 0
    votes = [f(h) for f in PREDICTORS]
    t_cnt = votes.count('T')
    confidence = round(t_cnt / len(votes), 2)
    return ('T' if t_cnt > len(votes)/2 else 'X'), confidence

# ==================== LẤY DỮ LIỆU THẬT ====================
def fetch_tele68():
    try:
        r = requests.get(API_URL, timeout=8)
        r.raise_for_status()
        data = r.json()
        if "list" in data and data["list"]:
            newest = data["list"][0]
            phien = newest.get("id")
            dice = newest.get("dices", [1, 2, 3])
            tong = newest.get("point", sum(dice))
            raw = newest.get("resultTruyenThong", "").upper()
            if raw == "TAI":
                ketqua = "Tài"
            elif raw == "XIU":
                ketqua = "Xỉu"
            else:
                ketqua = "Tài" if tong >= 11 else "Xỉu"
            return phien, dice, tong, ketqua
    except Exception as e:
        print("[❌] Lỗi fetch:", e)
    return None

# ==================== BACKGROUND UPDATER ====================
def background_updater():
    global last_data
    last_phien = None
    while True:
        data = fetch_tele68()
        if data:
            phien, dice, tong, ketqua = data
            if phien != last_phien and phien is not None:
                history_totals.append(tong)
                history_tx.append(ketqua)

                pred, conf = ensemble_predict(list(history_totals))

                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": pred,
                    "do_tin_cay": conf,
                    "id": "pentter99"
                }
                print(f"[✅] {phien} | {ketqua} ({tong}) | Dự đoán: {pred} ({conf})")
                last_phien = phien
        time.sleep(UPDATE_SEC)

# ==================== API ====================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

# ==================== MAIN ====================
if __name__ == "__main__":
    print("🚀 Khởi động API tài xỉu + 100 pentter thật...")
    threading.Thread(target=background_updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
