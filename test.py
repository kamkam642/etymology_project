import etymlib as et


def main():
    db = et.EtymologyData('./dict.json')
    db.langs['p-west-omaic']['<black>'].remove()
    print(db.roots)


if __name__ == '__main__':
    main()
