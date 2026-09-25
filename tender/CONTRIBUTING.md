# Contributing

**日本語版はこちら → [日本語](#日本語)**

## English

## Development Setup

```bash
conda activate cynovela
cd ~/Cynovela
bash start.sh
```

## Running Tests

```bash
python -m pytest tests/ -q
```

## Code Standards

- No organization names or proprietary product names in code, UI, or comments
- str_replace one item at a time
- Run pytest after every Python file change
- All tests must pass before committing

---

# 日本語

## 開発環境の準備

```bash
conda activate cynovela
cd ~/Cynovela
bash start.sh
```

## テストの実行

```bash
python -m pytest tests/ -q
```

## コードの決まり

- コード・画面・コメントに、企業名や商用製品の名前を書かない
- str_replace は一度に 1 か所ずつ行う
- Python のファイルを変えたら、そのつど pytest を実行する
- コミットの前に、テストがすべて通っていること
