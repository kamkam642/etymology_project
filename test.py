import etymlib as et


def main():
    db = et.EtymologyData('./graph.json')
    print(db.roots)
    db.write_dict_json('./dict.json')


if __name__ == '__main__':
    main()
