#!/bin/bash


if [ ! -f bbb_sunflower_1080p_30fps_normal.mp4 ]; then
    if [ ! -f bbb_sunflower_1080p_30fps_normal.mp4.zip ]; then
        wget https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip
    fi
    unzip bbb_sunflower_1080p_30fps_normal.mp4.zip
fi

if [ ! -f bbb.y4m ]; then
    ffmpeg -i bbb_sunflower_1080p_30fps_normal.mp4 -pix_fmt yuv420p bbb.y4m
fi

sed -i '0,/C420mpeg2/s//C420/' *.y4m