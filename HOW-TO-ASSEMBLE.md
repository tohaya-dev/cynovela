# How to assemble the split packages / 分割ファイルのつなぎ方

**日本語版はこちら → [日本語](#日本語)**

## English

The all-in-one packages are too large for a single download, so they are split
into parts of 1,500,000,000 bytes each. Do this once, before you start the tool.

1. Download **every** part of the package you picked, plus `SHA256SUMS`, into
   the same folder. If one part is missing, the result will be broken.

2. Join the parts in order:

       cat cynovela-falcon-all-in-one-20260817.tar.gz.part00 cynovela-falcon-all-in-one-20260817.tar.gz.part01 cynovela-falcon-all-in-one-20260817.tar.gz.part02 > cynovela-falcon-all-in-one-20260817.tar.gz

       cat cynovela-chewie-all-in-one-20260817.tar.gz.part00 cynovela-chewie-all-in-one-20260817.tar.gz.part01 cynovela-chewie-all-in-one-20260817.tar.gz.part02 > cynovela-chewie-all-in-one-20260817.tar.gz

   (`cat cynovela-falcon-all-in-one-20260817.tar.gz.part* > cynovela-falcon-all-in-one-20260817.tar.gz`
   does the same, because the shell sorts the part names.)

3. Check the result:

       shasum -a 256 --ignore-missing -c SHA256SUMS

   Every line it prints should say `OK`.

4. Unpack it:

       tar -xzf cynovela-falcon-all-in-one-20260817.tar.gz

       tar -xzf cynovela-chewie-all-in-one-20260817.tar.gz

If step 3 does not say `OK`: one of the parts did not download completely.
Download that part again and repeat from step 2. Do not start the tool with a
package that failed the check.

The two lightweight packages are single files and are not split. Unpack them
directly with `tar -xzf`.

For what to do next, see `STARTUP.md` in the folder you unpacked. If this is
your first time, `HAJIMETE.md` in the same folder is the gentler starting point.

---

# 日本語

全部入りは1つのファイルに収まらない大きさのため、片（1つ 1,500,000,000 バイト）に
割ってあります。使い始める前に、一度だけ次の作業をしてください。

1. 選んだ形の片を **全部** と、`SHA256SUMS` を、同じフォルダへ落とします。
   1つでも欠けると、つないだ結果が壊れます。

2. 片を順番につなぎます。

       cat cynovela-falcon-all-in-one-20260817.tar.gz.part00 cynovela-falcon-all-in-one-20260817.tar.gz.part01 cynovela-falcon-all-in-one-20260817.tar.gz.part02 > cynovela-falcon-all-in-one-20260817.tar.gz

       cat cynovela-chewie-all-in-one-20260817.tar.gz.part00 cynovela-chewie-all-in-one-20260817.tar.gz.part01 cynovela-chewie-all-in-one-20260817.tar.gz.part02 > cynovela-chewie-all-in-one-20260817.tar.gz

   （`cat cynovela-falcon-all-in-one-20260817.tar.gz.part* > cynovela-falcon-all-in-one-20260817.tar.gz`
   でも同じです。片の名前の順につながります。）

3. つないだ結果を確かめます。

       shasum -a 256 --ignore-missing -c SHA256SUMS

   出てきた行が `OK` と出れば成功です。

4. 取り出します。

       tar -xzf cynovela-falcon-all-in-one-20260817.tar.gz

       tar -xzf cynovela-chewie-all-in-one-20260817.tar.gz

3 で `OK` と出ない場合、どれかの片が最後まで落ちていません。その片を落とし直し、
2 からやり直してください。確かめに通らなかったものを使い始めないでください。

軽量版の2本は1つのファイルのままで、割ってありません。そのまま `tar -xzf` で
取り出せます。

以後の起動手順は、展開したフォルダの `STARTUP.md` をご覧ください。はじめての方は、
同じフォルダの `HAJIMETE.md` から読むほうが分かりやすいです。
