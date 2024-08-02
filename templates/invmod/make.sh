#! /usr/bin/env bash

./addchain/cmd/addchain/addchain search '15132376222941642752' > invmod.acc
./addchain/cmd/addchain/addchain gen -tmpl invmod.huff.template.template invmod.acc > invmod.huff.template
