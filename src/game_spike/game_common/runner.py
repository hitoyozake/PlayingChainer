#!/usr/bin/env python
# coding: utf-8

import os

from chainer import FunctionSet
import chainer.functions as F
from game_common.ascii_game_player_agent import agent_play, AsciiGamePlayerAgent
from game_common.agent_model import EmbedAgentModel


def calc_output_size(screen_size, ksize, stride):
    return (screen_size - ksize) / stride + 1


def run_pattern1(ThisGame, model_name):
    HISTORY_SIZE = 3
    PATTERN_SIZE1 = 50
    EMBED_OUT_SIZE = 3
    KSIZE1 = (3, 3*EMBED_OUT_SIZE)
    STRIDE1 = (1, 1*EMBED_OUT_SIZE)
    nw1 = calc_output_size(ThisGame.WIDTH*EMBED_OUT_SIZE, KSIZE1[1], STRIDE1[1])  # 13
    nh1 = calc_output_size(ThisGame.HEIGHT, KSIZE1[0], STRIDE1[0])                # 8

    PATTERN_SIZE2 = 100
    KSIZE2  = (3, 3)
    STRIDE2 = (1, 1)
    nw2 = calc_output_size(nw1, KSIZE2[1], STRIDE2[1])  # 11
    nh2 = calc_output_size(nh1, KSIZE2[0], STRIDE2[0])  # 6
    chainer_model = FunctionSet(
        l1=F.Convolution2D(HISTORY_SIZE, PATTERN_SIZE1, ksize=KSIZE1, stride=STRIDE1),
        l2=F.Convolution2D(PATTERN_SIZE1, PATTERN_SIZE2, ksize=KSIZE2, stride=STRIDE2),
        l3=F.Linear(nw2 * nh2 * PATTERN_SIZE2, 1000),
        l4=F.Linear(1000, 64),
    )
    model = EmbedAgentModel(model=chainer_model, model_name=model_name,
                            embed_out_size=EMBED_OUT_SIZE,
                            width=ThisGame.WIDTH, height=ThisGame.HEIGHT,
                            history_size=HISTORY_SIZE, out_size=64)

    def relu_with_drop_ratio(ratio):
        def f(x, train=True):
            return F.dropout(F.relu(x), train=train, ratio=ratio)
        return f

    def drop_ratio(ratio):
        def f(x, train=True):
            return F.dropout(x, train=train, ratio=ratio)
        return f

    model.activate_functions["l1"] = relu_with_drop_ratio(0.2)
    model.activate_functions["l2"] = relu_with_drop_ratio(0.4)
    model.activate_functions["l3"] = relu_with_drop_ratio(0.5)
    model.activate_functions["l4"] = drop_ratio(0.7)
    player = AsciiGamePlayerAgent(model)
    if os.environ.get("GPU"):
        player.setup_gpu(int(os.environ.get("GPU")))
    player.ALPHA = 0.01
    agent_play(ThisGame, player)
