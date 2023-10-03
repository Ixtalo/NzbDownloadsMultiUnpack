#!/bin/sh

set -x

## create dummy file with random content
head -c 20k </dev/urandom >rand.file


## -----------------------------------------------------------------------------
## RAR

## single RAR file, no split
mkdir -p rar_SingleNoSplit && pushd rar_SingleNoSplit
rar a -pfoobar0 "rand.{{foobar0}}.rar" ../rand.file
popd


## many splits (-v1 = 1 * 100 bytes)
mkdir -p rar_ManySplits && pushd rar_ManySplits 
rar a -pfoobar1 -v1 "rand.1.{{foobar1}}.rar" ../rand.file
popd

## less splits
mkdir -p rar_LessSplits && pushd rar_LessSplits
rar a -pfoobar2 -v10 "rand.2.{{foobar2}}.rar" ../rand.file
popd


## version 4 (-ma4), old naming style (-vn)
mkdir -p rar_v4 && pushd rar_v4
rar a -ma4 -pfoobar3 -vn -v10 "rand.3.{{foobar3}}.rar" ../rand.file
popd


## put RAR into subdir, the password is only in the directory name
mkdir -p "rar_example.dir.{{foobardir}}" && pushd "rar_example.dir.{{foobardir}}"
rar a -pfoobardir -v10 "rand.indir.rar" ../rand.file
popd


## multiple RARs in one directory
cp rand.file rand2.file
cp rand.file rand3.file
mkdir -p "rar_MultiRars{{foobardir}}" && pushd "rar_MultiRars{{foobardir}}"
rar a -pfoobardir -v10 "rand1.rar" ../rand.file
rar a -ma4 -vn -v20 "rand2.rar" ../rand2.file
rar a "rand3.single.rar" ../rand3.file
popd


## -----------------------------------------------------------------------------
## 7z

## put into subdir, the password is only in the directory name
mkdir -p "7z_example.dir.{{foobardir}}" && pushd "7z_example.dir.{{foobardir}}"
7z a -pfoobardir -v10k "rand.indir.7z" ../rand.file
popd

## put into subdir with spaces, the password is only in the directory name
mkdir -p "7z_example dir {{foobardir}}" && pushd "7z_example dir {{foobardir}}"
7z a -pfoobardir -v10k "rand with spaces.7z" ../rand.file
popd
