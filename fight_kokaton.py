import os
import random
import sys
import time
import math

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]
NUM_OF_BOMBS = 5  # 爆弾の数


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとん，または，爆弾SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        img0 = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
        self.imgs = {  # 0度から反時計回りに定義
            (+5, 0): img,  # 右
            (+5, -5): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -5): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-5, -5): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-5, 0): img0,  # 左
            (-5, +5): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +5): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+5, +5): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        # self.img = pg.transform.flip(  # 左右反転
        #     pg.transform.rotozoom(  # 2倍に拡大
        #         pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 
        #         0, 
        #         2.0), 
        #     True, 
        #     False
        # )
        self.img = self.imgs[(+5, 0)]  # 右向きこうかとんをデフォルトにする
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.dire = [+5,0]  # 方向タプル用

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
            
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not(sum_mv[0]==0 and sum_mv[1]==0):  # 何かキーが押されていたら
            self.img = self.imgs[tuple(sum_mv)]
            self.dire = sum_mv
        screen.blit(self.img, self.rct)


class Bomb:
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    directions = [-5, +5]
    """
    爆弾に関するクラス
    """
    def __init__(self):
        """
        爆弾円Surfaceを生成する
        """
        rad = random.randint(10, 100)
        self.img = pg.Surface((2*rad, 2*rad))
        color = random.choice(Bomb.colors)
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = random.choice(Bomb.directions), random.choice(Bomb.directions)

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Beam:
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像を生成する
        引数bird:こうかとんに関する情報
        """
        self.img = pg.image.load(f"{MAIN_DIR}/fig/beam.png")
        self.rct = self.img.get_rect()
        self.vx, self.vy = bird.dire
        self.rct.centerx = bird.rct.centerx + bird.rct.width*self.vx/5
        self.rct.centery = bird.rct.centery + bird.rct.height*self.vy/5
        atan = math.atan2(-self.vy, self.vx)
        deg = math.degrees(atan)
        self.img = pg.transform.rotozoom(self.img, deg, 1.0)
        
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: Bomb):
        """
        爆発エフェクトを生成する
        引数bomb:爆弾の消滅位置
        """
        exp = pg.image.load(f"{MAIN_DIR}/fig/explosion.gif")
        self.exps = [pg.transform.rotozoom(exp, 90.0*i, 1.0) for i in range(4)]  # 角度の違う画像を4つ格納
        self.dirx, self.diry = bomb.rct.centerx, bomb.rct.centery
        self.life = 4

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを表示する
        引数 screen：画面Surface
        """
        self.life = self.life-1
        screen.blit(self.exps[self.life], (self.dirx, self.diry))


class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        スコアをhgp創英角ﾎﾟｯﾌﾟ体で生成する
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.font.render(f"スコア:{self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.centerx, self.rct.centery = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        """
        スコアを表示する
        引数screen:画面Surface
        """
        scr = self.font.render(f"スコア:{self.score}", 0, self.color)
        screen.blit(scr, self.rct)


def main():
    """
    メインの処理をする関数
    """
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load(f"{MAIN_DIR}/fig/pg_bg.jpg")
    bird = Bird(3, (900, 400))
    bombs = [Bomb() for _ in range(NUM_OF_BOMBS)]  # NUM_OF_BOMBS個のBombインスタンス
    # beam = None
    exp = list()  # Explosionインスタンス格納用
    score = Score()  # Scoreインスタンス生成
    mbeam = list()  # Beamインスタンス格納用

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:  # キーが押されたら
                mbeam.append(Beam(bird))  # Beamインスタンスを格納
        
        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return
        
        for i, bomb in enumerate(bombs):
            for j, beam in enumerate(mbeam):
                if beam is None:  # beamがNoneなら、以降の処理を飛ばす(バグ防止)
                    continue
                if beam.rct.colliderect(bomb.rct):  # 爆弾とビームがぶつかったら
                    bombs[i] = None
                    mbeam[j] = None
                    score.score += 1  # スコア+1
                    exp.append(Explosion(bomb))
                    bird.change_img(6, screen)

        bombs = [bomb for bomb in bombs if bomb is not None]  # Noneでない爆弾だけのリスト
        exp = [e for e in exp if e.life > 0]  # lifeが0より大きいexpだけをリスト化
        mbeam = [m for m in mbeam if m is not None and(0<m.rct.centerx<WIDTH and 0<m.rct.centery<HEIGHT) ]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for bomb in bombs:
            bomb.update(screen)
        if mbeam:  # もしmbeamに中身があれば
            for beam in mbeam:
                beam.update(screen)
        if exp:  # もしexpに中身があれば
            for e in exp:
                e.update(screen)  # expの中身をupdate
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
