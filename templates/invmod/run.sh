#! /usr/bin/env bash

./addchain/cmd/addchain/addchain search '4002409555221667393417789825735904156556882819939007885332058136124031650490837864442687629129015664037894272559785' > invmod.acc
./addchain/cmd/addchain/addchain gen -tmpl invmod.huff.template.template invmod.acc > invmod.huff.template
