#!/bin/bash

set -x

## create dummy file with random content
[[ rand.file ]] || head -c 20k </dev/urandom >rand.file
[[ rand2.file ]] || cp rand.file rand2.file
[[ rand3.file ]] || cp rand.file rand3.file


## -----------------------------------------------------------------------------
## RAR

## single RAR file, no split
mkdir -p rar_SingleNoSplit && pushd rar_SingleNoSplit
rar a -pfoobar0 "rand.{{foobar0}}.rar" ../rand.file
touch "rand.{{foobar0}}.par2"
popd


## many splits (-v1 = 1 * 100 bytes)
mkdir -p rar_ManySplits && pushd rar_ManySplits
rar a -y -pfoobar1 -v1 "rand.1.{{foobar1}}.rar" ../rand.file
touch "rand.1.{{foobar1}}.par2"
popd

## less splits
mkdir -p rar_LessSplits && pushd rar_LessSplits
rar a -y -pfoobar2 -v10 "rand.2.{{foobar2}}.rar" ../rand.file
touch "rand.2.{{foobar2}}.par2"
popd


## version 4 (-ma4), old naming style (-vn)
mkdir -p rar_v4 && pushd rar_v4
rar a -y -ma4 -pfoobar3 -vn -v10 "rand.3.{{foobar3}}.rar" ../rand.file
touch "rand.3.{{foobar3}}.par2"
popd


## put RAR into subdir, the password is only in the directory name
mkdir -p "rar_example.dir.{{foobardir}}" && pushd "rar_example.dir.{{foobardir}}"
rar a -y -pfoobardir -v10 "rand.indir.rar" ../rand.file
touch "rand.indir.par2"
popd


## multiple RARs in one directory
mkdir -p "rar_MultiRars{{foobardir}}" && pushd "rar_MultiRars{{foobardir}}"
rar a -y -pfoobardir -v10 "rand1.rar" ../rand.file
rar a -y -ma4 -vn -v20 "rand2.rar" ../rand2.file
rar a -y "rand3.single.rar" ../rand3.file
popd


## -----------------------------------------------------------------------------
## 7z

## put into subdir, the password is only in the directory name
mkdir -p "7z_example.dir.{{foobardir}}" && pushd "7z_example.dir.{{foobardir}}"
7z a -y -pfoobardir -v10k "rand.indir.7z" ../rand.file
touch "rand.indir.par2"
popd

## put into subdir with spaces, the password is only in the directory name
mkdir -p "7z_example dir {{foobardir}}" && pushd "7z_example dir {{foobardir}}"
7z a -y -pfoobardir -v10k "rand with spaces.7z" ../rand.file
touch "rand with spaces.par2"
popd
