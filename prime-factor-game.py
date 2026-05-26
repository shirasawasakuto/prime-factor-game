import random
import tkinter as tk
from tkinter import ttk, messagebox

# ==============================
# ロジック関数
# ==============================

def prime_factorize(n: int) -> list:
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def is_correct(n: int, factors: list) -> bool:
    if not factors:
        return False
    for f in factors:
        if f < 2 or prime_factorize(f) != [f]:
            return False
    product = 1
    for f in factors:
        product *= f
    return product == n

def parse_factors(s: str) -> list | None:
    try:
        s = s.replace("×", " ").replace("*", " ").replace("x", " ")
        tokens = s.split()
        factors = []
        for t in tokens:
            if "^" in t:
                base, exp = t.split("^")
                factors.extend([int(base)] * int(exp))
            else:
                v = int(t)
                if v >= 2:
                    factors.append(v)
        return factors if factors else None
    except Exception:
        return None

def generate_topic(digits: int) -> int:
    low = 10 ** (digits - 1)
    high = 10 ** digits - 1
    return random.randint(low, high)

def digit_count(n: int) -> int:
    return len(str(n))

# ==============================
# カラーテーマ
# ==============================
BG       = "#1e1e2e"
PANEL    = "#2a2a3e"
ACCENT   = "#7c6af7"
ACCENT2  = "#f7a26a"
TEXT     = "#e0e0f0"
GREEN    = "#5af78e"
RED      = "#f7605a"
YELLOW   = "#f7e45a"
GRAY     = "#555570"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_HEAD  = ("Helvetica", 14, "bold")
FONT_BODY  = ("Helvetica", 12)
FONT_SMALL = ("Helvetica", 10)
FONT_MONO  = ("Courier", 13, "bold")
FONT_TIMER = ("Helvetica", 28, "bold")

# ==============================
# ゲームアプリ本体
# ==============================

class PrimeFactorGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("素因数分解バトル")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("700x600")

        self.players = []
        self.digits = 2
        self.wins = {}
        self.round_num = 0
        self.topic = 0
        self.chosen = {}
        self.submitted = {}
        self.phase = "setup"
        self.current_player_idx = 0

        # 制限時間
        self.time_limit_on = tk.BooleanVar(value=False)
        self.time_limit_sec = tk.IntVar(value=30)
        self._timer_id = None      # after() のID
        self._remaining = 0        # 残り秒数
        self._timer_label = None   # タイマー表示ラベル

        self._show_setup()

    # ---------- 画面クリア ----------
    def _clear(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        for w in self.winfo_children():
            w.destroy()

    # ---------- 共通ウィジェット ----------
    def _label(self, parent, text, font=FONT_BODY, fg=TEXT, bg=None, **kw):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg or BG, **kw)

    def _button(self, parent, text, cmd, color=ACCENT, width=18):
        return tk.Button(parent, text=text, command=cmd,
                         font=FONT_HEAD, bg=color, fg="white",
                         activebackground=color, relief="flat",
                         cursor="hand2", width=width, pady=6)

    def _entry(self, parent, textvariable=None, width=20):
        return tk.Entry(parent, textvariable=textvariable,
                        font=FONT_MONO, bg=PANEL, fg=TEXT,
                        insertbackground=TEXT, relief="flat",
                        width=width, justify="center")

    def _panel(self, parent, **kw):
        return tk.Frame(parent, bg=PANEL, **kw)

    # ---------- ① セットアップ画面 ----------
    def _show_setup(self):
        self._clear()
        self.phase = "setup"

        self._label(self, "⚡ 素因数分解バトル ⚡", FONT_TITLE, ACCENT).pack(pady=(24, 4))
        self._label(self, "BO3 形式で素因数の多さを競え！", FONT_SMALL, GRAY).pack(pady=(0, 16))

        frame = self._panel(self, padx=30, pady=16)
        frame.pack(padx=40, fill="x")

        # プレイヤー数
        self._label(frame, "プレイヤー数", FONT_HEAD, TEXT, PANEL).grid(row=0, column=0, sticky="w", pady=6)
        self.num_var = tk.IntVar(value=2)
        tk.Spinbox(frame, from_=2, to=4, textvariable=self.num_var,
                   font=FONT_BODY, width=5, bg=PANEL, fg=TEXT,
                   buttonbackground=ACCENT, relief="flat",
                   command=self._update_name_fields).grid(row=0, column=1, sticky="w", padx=10)

        # 名前入力
        self.name_frame = self._panel(frame)
        self.name_frame.grid(row=1, column=0, columnspan=4, pady=8, sticky="ew")
        self.name_vars = []
        self._update_name_fields()

        # 桁数
        self._label(frame, "お題の桁数", FONT_HEAD, TEXT, PANEL).grid(row=2, column=0, sticky="w", pady=6)
        self.digit_var = tk.IntVar(value=2)
        for i, d in enumerate([2, 3, 4]):
            tk.Radiobutton(frame, text=f"{d}桁", variable=self.digit_var, value=d,
                           font=FONT_BODY, bg=PANEL, fg=TEXT,
                           selectcolor=PANEL, activebackground=PANEL,
                           activeforeground=ACCENT).grid(row=2, column=1 + i, sticky="w")

        # 難易度
        self._label(frame, "難易度", FONT_HEAD, TEXT, PANEL).grid(row=3, column=0, sticky="w", pady=6)
        self.hard_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="高難易度（素因数の種類数で競う）",
                       variable=self.hard_mode,
                       font=FONT_BODY, bg=PANEL, fg=TEXT,
                       selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=ACCENT).grid(row=3, column=1, columnspan=3, sticky="w")

        # 制限時間
        self._label(frame, "制限時間", FONT_HEAD, TEXT, PANEL).grid(row=4, column=0, sticky="w", pady=6)
        tk.Checkbutton(frame, text="あり", variable=self.time_limit_on,
                       font=FONT_BODY, bg=PANEL, fg=TEXT,
                       selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=ACCENT,
                       command=self._toggle_time_limit).grid(row=4, column=1, sticky="w")

        self.time_spin_frame = tk.Frame(frame, bg=PANEL)
        self.time_spin_frame.grid(row=4, column=2, columnspan=2, sticky="w")
        self.time_spin = tk.Spinbox(self.time_spin_frame, from_=10, to=120, increment=5,
                                    textvariable=self.time_limit_sec,
                                    font=FONT_BODY, width=5, bg=PANEL, fg=TEXT,
                                    buttonbackground=ACCENT, relief="flat")
        self.time_spin.pack(side="left")
        self._label(self.time_spin_frame, " 秒", FONT_BODY, GRAY, PANEL).pack(side="left")
        self._toggle_time_limit()

        self._button(self, "ゲームスタート！", self._start_game).pack(pady=20)

    def _toggle_time_limit(self):
        state = "normal" if self.time_limit_on.get() else "disabled"
        self.time_spin.config(state=state)

    def _update_name_fields(self):
        for w in self.name_frame.winfo_children():
            w.destroy()
        self.name_vars = []
        defaults = ["Alice", "Bob", "Carol", "Dave"]
        n = self.num_var.get()
        for i in range(n):
            v = tk.StringVar(value=defaults[i])
            self.name_vars.append(v)
            tk.Label(self.name_frame, text=f"P{i+1} 名前:", font=FONT_SMALL,
                     bg=PANEL, fg=TEXT).grid(row=i, column=0, sticky="w", pady=2)
            self._entry(self.name_frame, v, width=14).grid(row=i, column=1, padx=8, pady=2)

    def _start_game(self):
        names = [v.get().strip() or f"P{i+1}" for i, v in enumerate(self.name_vars)]
        self.players = names
        self.digits = self.digit_var.get()
        self.is_hard = self.hard_mode.get()
        self.wins = {p: 0 for p in self.players}
        self.round_num = 0
        self._next_round()

    def _score(self, factors: list) -> int:
        """難易度に応じて素因数のスコアを返す"""
        return len(set(factors)) if self.is_hard else len(factors)

    # ---------- ② ラウンド開始 ----------
    def _next_round(self):
        self.round_num += 1
        self.topic = generate_topic(self.digits)
        self.chosen = {}
        self.submitted = {}
        self.current_player_idx = 0
        self._show_choose_phase()

    # ---------- ③ 数の選択フェーズ ----------
    def _show_choose_phase(self):
        self._clear()
        self.phase = "choose"
        p = self.players[self.current_player_idx]

        self._draw_header()
        self._label(self, "【数の選択フェーズ】", FONT_HEAD, ACCENT2).pack(pady=(10, 2))
        self._label(self, f"お題より大きく、{self.digits}桁の数を選んでください", FONT_SMALL, GRAY).pack()

        panel = self._panel(self, padx=30, pady=16)
        panel.pack(padx=40, pady=8, fill="x")

        topic_box = self._panel(panel, padx=20, pady=8)
        topic_box.pack(fill="x", pady=(0, 12))
        self._label(topic_box, "お　題", FONT_SMALL, GRAY, PANEL).pack()
        self._label(topic_box, str(self.topic), ("Helvetica", 36, "bold"), YELLOW, PANEL).pack()

        self._label(panel, f"{p} の番", FONT_HEAD, TEXT, PANEL).pack(pady=(0, 6))
        self.choose_var = tk.StringVar()
        e = self._entry(panel, self.choose_var, width=14)
        e.pack()
        e.focus()
        e.bind("<Return>", lambda _: self._submit_choose())
        self._label(panel, f"（{self.topic} より大きく {self.digits}桁の整数）",
                    FONT_SMALL, GRAY, PANEL).pack(pady=4)
        self.choose_err = self._label(panel, "", FONT_SMALL, RED, PANEL)
        self.choose_err.pack()

        self._button(self, "決定", self._submit_choose).pack(pady=10)

    def _submit_choose(self):
        p = self.players[self.current_player_idx]
        raw = self.choose_var.get().strip()
        try:
            n = int(raw)
        except ValueError:
            self.choose_err.config(text="整数を入力してください。")
            return
        if digit_count(n) != self.digits:
            self.choose_err.config(text=f"{self.digits}桁の数を入力してください。")
            return
        if n <= self.topic:
            self.choose_err.config(text=f"{self.topic} より大きい数を入力してください。")
            return

        self.chosen[p] = n
        self.current_player_idx += 1
        if self.current_player_idx < len(self.players):
            self._show_choose_phase()
        else:
            self.current_player_idx = 0
            self._show_factorize_phase()

    # ---------- ④ 素因数分解フェーズ ----------
    def _show_factorize_phase(self):
        self._clear()
        self.phase = "factorize"
        self.submitted = {}
        self.current_player_idx = 0
        self._show_factorize_for_current()

    def _show_factorize_for_current(self):
        self._clear()
        p = self.players[self.current_player_idx]
        n = self.chosen[p]

        self._draw_header()
        self._label(self, "【素因数分解フェーズ】", FONT_HEAD, ACCENT2).pack(pady=(10, 2))
        self._label(self, "素因数分解を入力してください", FONT_SMALL, GRAY).pack()

        panel = self._panel(self, padx=30, pady=16)
        panel.pack(padx=40, pady=8, fill="x")

        self._label(panel, f"{p} の番", FONT_HEAD, TEXT, PANEL).pack(pady=(0, 6))

        num_box = self._panel(panel, padx=16, pady=6)
        num_box.pack(fill="x", pady=(0, 10))
        self._label(num_box, "選んだ数", FONT_SMALL, GRAY, PANEL).pack()
        self._label(num_box, str(n), ("Helvetica", 30, "bold"), ACCENT, PANEL).pack()

        # タイマー表示
        if self.time_limit_on.get():
            self._remaining = self.time_limit_sec.get()
            timer_box = self._panel(panel, padx=10, pady=4)
            timer_box.pack(fill="x", pady=(0, 6))
            self._label(timer_box, "残り時間", FONT_SMALL, GRAY, PANEL).pack()
            self._timer_label = tk.Label(timer_box, text=f"{self._remaining}",
                                         font=FONT_TIMER, fg=GREEN, bg=PANEL)
            self._timer_label.pack()
            self._tick()

        self._label(panel, "入力例: 2 2 3  /  2^2*3  /  2×2×3", FONT_SMALL, GRAY, PANEL).pack(pady=(0, 4))
        self.factor_var = tk.StringVar()
        self._factor_entry = self._entry(panel, self.factor_var, width=22)
        self._factor_entry.pack()
        self._factor_entry.focus()
        self._factor_entry.bind("<Return>", lambda _: self._submit_factors())

        self.factor_err = self._label(panel, "", FONT_SMALL, RED, PANEL)
        self.factor_err.pack(pady=4)

        self._submit_btn = self._button(self, "提出", self._submit_factors)
        self._submit_btn.pack(pady=10)

    # ---------- タイマー処理 ----------
    def _tick(self):
        if self._timer_label is None:
            return
        if self._remaining <= 0:
            self._timer_label.config(text="0", fg=RED)
            self._time_up()
            return

        # 残り5秒以下は赤に
        color = RED if self._remaining <= 5 else (YELLOW if self._remaining <= 10 else GREEN)
        self._timer_label.config(text=str(self._remaining), fg=color)
        self._remaining -= 1
        self._timer_id = self.after(1000, self._tick)

    def _time_up(self):
        """時間切れ → 空の回答として強制提出"""
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        # 入力欄・ボタンを無効化
        try:
            self._factor_entry.config(state="disabled")
            self._submit_btn.config(state="disabled")
        except Exception:
            pass
        p = self.players[self.current_player_idx]
        self.submitted[p] = []  # 空＝不正解扱い
        # 0.8秒後に次へ
        self.after(800, self._advance_factorize)

    # ---------- 素因数提出 ----------
    def _submit_factors(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        p = self.players[self.current_player_idx]
        raw = self.factor_var.get().strip()
        factors = parse_factors(raw)
        if factors is None:
            self.factor_err.config(text="入力形式が正しくありません。例: 2 2 3 / 2^2*3")
            # タイマーを再開
            if self.time_limit_on.get() and self._remaining > 0:
                self._tick()
            return
        self.submitted[p] = factors
        self._advance_factorize()

    def _advance_factorize(self):
        self.current_player_idx += 1
        if self.current_player_idx < len(self.players):
            self._show_factorize_for_current()
        else:
            self._show_result()

    # ---------- ⑤ 結果フェーズ ----------
    def _show_result(self):
        self._clear()
        self._draw_header()
        self._label(self, "【判定結果】", FONT_HEAD, ACCENT2).pack(pady=(10, 4))

        correct = {}
        result_frame = self._panel(self, padx=20, pady=8)
        result_frame.pack(padx=30, fill="x")

        mode_label = "素因数の種類数" if self.is_hard else "素因数の個数"
        for p in self.players:
            n = self.chosen[p]
            factors = self.submitted.get(p, [])
            real = prime_factorize(n)
            ok = is_correct(n, factors)

            row = self._panel(result_frame, padx=12, pady=6)
            row.pack(fill="x", pady=3)

            color = GREEN if ok else RED
            icon  = "✅" if ok else "❌"
            factor_str = " × ".join(map(str, real))

            header = "時間切れ ⏰" if (not factors and self.time_limit_on.get()) else icon
            self._label(row, f"{header}  {p}", FONT_HEAD, color, PANEL).pack(anchor="w")
            self._label(row, f"  選んだ数: {n}　→　{n} = {factor_str}", FONT_BODY, TEXT, PANEL).pack(anchor="w")
            if ok:
                sc = self._score(real)
                self._label(row, f"  {mode_label}: {sc}", FONT_SMALL, GRAY, PANEL).pack(anchor="w")
                correct[p] = real
            else:
                sub_str = " × ".join(map(str, factors)) if factors else "（未回答）"
                self._label(row, f"  あなたの答え: {sub_str}", FONT_SMALL, RED, PANEL).pack(anchor="w")

        # 勝者判定
        if not correct:
            round_result = "全員不正解！両者敗北。"
            round_winners = []
        else:
            max_sc = max(self._score(v) for v in correct.values())
            round_winners = [p for p, v in correct.items() if self._score(v) == max_sc]
            if len(round_winners) == 1:
                round_result = f"🏆 {round_winners[0]} の勝利！（{mode_label} {max_sc}）"
                self.wins[round_winners[0]] += 1
            else:
                round_result = f"同点！両者敗北。（{' vs '.join(round_winners)}、{mode_label} {max_sc}）"

        res_box = self._panel(self, padx=16, pady=8)
        res_box.pack(padx=30, fill="x", pady=4)
        self._label(res_box, round_result, FONT_HEAD, YELLOW, PANEL).pack()

        score_box = self._panel(self, padx=16, pady=6)
        score_box.pack(padx=30, fill="x")
        self._label(score_box, "スコア", FONT_SMALL, GRAY, PANEL).pack()
        score_row = tk.Frame(score_box, bg=PANEL)
        score_row.pack()
        for p in self.players:
            self._label(score_row, f"{p}: {self.wins[p]}勝", FONT_HEAD, ACCENT, PANEL).pack(side="left", padx=14)

        champion = [p for p, w in self.wins.items() if w >= 2]
        # 高難易度: 勝者が出るまでエンドレス（BO3なし）
        # 通常: 2勝先取でゲーム終了
        threshold = 3 if self.is_hard else 2
        champion = [p for p, w in self.wins.items() if w >= threshold]
        if champion:
            self._button(self, "🎉 結果発表！", lambda: self._show_champion(champion[0]), color=GREEN).pack(pady=10)
        else:
            self._button(self, "次のラウンドへ →", self._next_round).pack(pady=10)

    # ---------- ⑥ 優勝画面 ----------
    def _show_champion(self, champion: str):
        self._clear()
        self._label(self, "🎉 ゲーム終了！ 🎉", FONT_TITLE, YELLOW).pack(pady=(44, 14))

        box = self._panel(self, padx=40, pady=24)
        box.pack(padx=60, fill="x")
        self._label(box, "優　勝", FONT_HEAD, GRAY, PANEL).pack()
        self._label(box, champion, ("Helvetica", 32, "bold"), GREEN, PANEL).pack(pady=8)
        self._label(box, "最終スコア", FONT_SMALL, GRAY, PANEL).pack(pady=(10, 4))
        for p in self.players:
            color = GREEN if p == champion else TEXT
            self._label(box, f"{p}：{self.wins[p]} 勝", FONT_HEAD, color, PANEL).pack()

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=20)
        self._button(btn_row, "もう一度遊ぶ", self._restart, color=ACCENT, width=16).pack(side="left", padx=10)
        self._button(btn_row, "終了", self.quit, color=GRAY, width=10).pack(side="left", padx=10)

    def _restart(self):
        self.wins = {}
        self.round_num = 0
        self._show_setup()

    # ---------- ヘッダー ----------
    def _draw_header(self):
        hdr = self._panel(self, padx=20, pady=6)
        hdr.pack(fill="x")
        limit = "先取" if self.is_hard else "/ 3"
        num = "3勝" if self.is_hard else str(self.round_num)
        self._label(hdr, f"ラウンド {self.round_num}  {'（3勝先取）' if self.is_hard else '/ 3'}", FONT_HEAD, ACCENT, PANEL).pack(side="left")
        score_str = "   ".join(f"{p}: {self.wins[p]}W" for p in self.players)
        self._label(hdr, score_str, FONT_SMALL, GRAY, PANEL).pack(side="right")
        self._label(hdr, f"お題: {self.topic}", FONT_HEAD, YELLOW, PANEL).pack()

# ==============================
# エントリーポイント
# ==============================

if __name__ == "__main__":
    app = PrimeFactorGame()
    app.mainloop()
