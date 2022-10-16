#!/bin/sh

## create dummy file with random content
head -c 20k </dev/urandom >rand

## single RAR file, no split
rar a -pfoobar0 "rand.0.{{foobar0}}.rar" rand

## many splits (-v1 = 1 * 100 bytes)
rar a -pfoobar1 -v1 "rand.1.{{foobar1}}.rar" rand

## less splits
rar a -pfoobar2 -v10 "rand.2.{{foobar2}}.rar" rand


## version 4 (-ma4), old naming style (-vn)
rar a -ma4 -pfoobar3 -vn -v10 "rand.3.{{foobar3}}.rar" rand

## another version 4 (-ma4), old naming style (-vn)
rar a -ma4 -pfoobar4 -vn -v10 "rand.4.{{foobar4}}.rar" rand


## put RAR into subdir, the password is only in the directory name
mkdir -p "example.dir.{{foobardir}}"
pushd "example.dir.{{foobardir}}"
rar a -pfoobardir -v10 "rand.indir.rar" ../rand
