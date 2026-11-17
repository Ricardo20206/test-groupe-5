"""Tests stratégie agressive anti-classement."""

from __future__ import annotations

from dopynion.data_model import CardName, Cards, Game, Player

from strategy import (
    choose_action,
    choose_buy,
    choose_discard,
    choose_gain,
    choose_money_to_upgrade,
    choose_trash,
    confirm_discard,
    confirm_trash,
    decide_play,
    end_game_state,
    init_game,
    reset_turn,
    skip_reception,
    _memory,
)


def make_game(
    hand: dict[CardName, int],
    *,
    provinces: int = 8,
    stock: dict[CardName, int] | None = None,
    n_players: int = 2,
) -> Game:
    base: dict[CardName, int] = {
        CardName.PROVINCE: provinces,
        CardName.GOLD: 30,
        CardName.SILVER: 40,
        CardName.DUCHY: 8,
        CardName.ESTATE: 8,
        CardName.CURSE: 30,
        CardName.COPPER: 60,
        CardName.GARDENS: 12,
    }
    if stock:
        base.update(stock)
    players = [
        Player(name="BotMatch", hand=Cards(quantities=hand), score=0),
        Player(name="Adverse", hand=None, score=0),
    ]
    for i in range(max(0, n_players - 2)):
        players.append(Player(name=f"P{i}", hand=None, score=0))
    return Game(
        finished=False,
        players=players,
        stock=Cards(quantities=base),
    )


def stock(extra: dict[CardName, int] | None = None) -> dict[CardName, int]:
    base = {
        CardName.MILITIA: 10,
        CardName.WITCH: 10,
        CardName.FARMINGVILLAGE: 10,
        CardName.FESTIVAL: 10,
        CardName.VILLAGE: 10,
        CardName.LABORATORY: 10,
        CardName.SMITHY: 10,
        CardName.BANDIT: 10,
        CardName.HIRELING: 10,
        CardName.CHAPEL: 10,
        CardName.MARKET: 10,
        CardName.GARDENS: 12,
        CardName.FORTUNETELLER: 10,
        CardName.COUNCILROOM: 10,
    }
    if extra:
        base.update(extra)
    return base


def check(label: str, got: object, expected: object) -> None:
    status = "OK" if got == expected else "FAIL"
    print(f"  [{status}] {label}: {got!r} (attendu {expected!r})")
    assert got == expected, f"{label}: {got!r} != {expected!r}"


def main() -> None:
    init_game("prio")
    mem = _memory("prio")

    check("$3 silver (pas chapel a 3)", choose_buy(make_game({}), 3, mem), CardName.SILVER)
    check(
        "$3 silver meme si witch kingdom",
        choose_buy(make_game({}, stock=stock()), 3, mem),
        CardName.SILVER,
    )
    check("$6 gold", choose_buy(make_game({}), 6, mem), CardName.GOLD)
    check("$8 province", choose_buy(make_game({}), 8, mem), CardName.PROVINCE)
    check(
        "$5 witch",
        choose_buy(make_game({}, stock=stock()), 5, mem),
        CardName.WITCH,
    )
    mem.bought[CardName.WITCH] = 2
    check(
        "$5 apres witches -> festival",
        choose_buy(make_game({}, stock=stock()), 5, mem),
        CardName.FESTIVAL,
    )
    mem.bought[CardName.FESTIVAL] = 2
    check(
        "$5 apres festival -> laboratory",
        choose_buy(make_game({}, stock=stock({CardName.BANDIT: 0})), 5, mem),
        CardName.LABORATORY,
    )
    mem.bought[CardName.LABORATORY] = 2
    check(
        "$5 apres lab -> mine",
        choose_buy(
            make_game({}, stock=stock({CardName.MINE: 10, CardName.BANDIT: 0})),
            5,
            mem,
        ),
        CardName.MINE,
    )
    mem.bought.clear()
    check(
        "$4 militia prioritaire",
        choose_buy(make_game({}, stock=stock()), 4, mem),
        CardName.MILITIA,
    )
    mem.bought.clear()
    mem.bought[CardName.MILITIA] = 1
    mem.bought[CardName.WITCH] = 1
    check(
        "$4 village apres terminale",
        choose_buy(make_game({}, stock=stock()), 4, mem),
        CardName.FARMINGVILLAGE,
    )
    mem.bought[CardName.FARMINGVILLAGE] = 1
    check(
        "$4 smithy soutien apres attaques",
        choose_buy(
            make_game({}, stock=stock({CardName.MONEYLENDER: 10})),
            4,
            mem,
        ),
        CardName.SMITHY,
    )

    mem.bought.clear()
    check(
        "$6 or d abord",
        choose_buy(make_game({}, stock=stock({CardName.HIRELING: 10})), 6, mem),
        CardName.GOLD,
    )
    mem.bought[CardName.GOLD] = 1
    check(
        "$6 hireling apres 1 or",
        choose_buy(make_game({}, stock=stock({CardName.HIRELING: 10})), 6, mem),
        CardName.HIRELING,
    )
    check(
        "$11 pas de colonie -> province",
        choose_buy(
            make_game({}, stock=stock({CardName.COLONY: 10})),
            11,
            mem,
        ),
        CardName.PROVINCE,
    )

    mem.bought.clear()
    check(
        "$5 p5 pas encore duchy (2j) -> witch",
        choose_buy(make_game({}, provinces=5, stock=stock()), 5, mem),
        CardName.WITCH,
    )
    check(
        "$5 p3 duchy (2j)",
        choose_buy(make_game({}, provinces=3, stock=stock()), 5, mem),
        CardName.DUCHY,
    )
    check(
        "$4 p4 gardens (2j)",
        choose_buy(make_game({}, provinces=4, stock=stock()), 4, mem),
        CardName.GARDENS,
    )
    check(
        "$5 p5 duchy (3j)",
        choose_buy(
            make_game({}, provinces=5, stock=stock(), n_players=3),
            5,
            mem,
        ),
        CardName.DUCHY,
    )
    check(
        "$2 p3 estate",
        choose_buy(make_game({}, provinces=3, stock=stock()), 2, mem),
        CardName.ESTATE,
    )
    check(
        "$2 chapel si witch kingdom",
        choose_buy(make_game({}, stock=stock()), 2, mem),
        CardName.CHAPEL,
    )

    mem.bought.clear()
    check(
        "$4 plateau calme -> silver (pas smithy/CR)",
        choose_buy(
            make_game(
                {},
                stock={
                    CardName.SMITHY: 10,
                    CardName.COUNCILROOM: 10,
                    CardName.LIBRARY: 10,
                    CardName.ADVENTURER: 10,
                },
            ),
            4,
            mem,
        ),
        CardName.SILVER,
    )
    check(
        "$5 p8 duchy plateau calme (3j style Bowser)",
        choose_buy(
            make_game(
                {},
                provinces=8,
                n_players=3,
                stock={
                    CardName.SMITHY: 10,
                    CardName.LIBRARY: 10,
                    CardName.ADVENTURER: 10,
                },
            ),
            5,
            mem,
        ),
        CardName.DUCHY,
    )

    chapel_hand = Cards(
        quantities={CardName.CHAPEL: 1, CardName.COPPER: 2, CardName.WITCH: 1}
    )
    check(
        "joue chapel avec copper",
        choose_action(chapel_hand, make_game({}, stock=stock())),
        CardName.CHAPEL,
    )

    fv_hand = Cards(
        quantities={
            CardName.FESTIVAL: 1,
            CardName.FARMINGVILLAGE: 1,
            CardName.WITCH: 1,
        }
    )
    check(
        "festival avant farming village",
        choose_action(fv_hand, make_game({}, stock=stock())),
        CardName.FESTIVAL,
    )
    check(
        "witch avant militia",
        choose_action(
            Cards(quantities={CardName.WITCH: 1, CardName.MILITIA: 1}),
            make_game({}, stock={CardName.CURSE: 10}),
        ),
        CardName.WITCH,
    )
    check(
        "militia avant smithy",
        choose_action(
            Cards(quantities={CardName.MILITIA: 1, CardName.SMITHY: 1}),
            make_game({}, stock=stock()),
        ),
        CardName.MILITIA,
    )

    end_game_state("t1")
    init_game("t1")
    reset_turn("t1")
    gs = make_game(
        {CardName.FESTIVAL: 1, CardName.GOLD: 1, CardName.COPPER: 2},
        stock=stock(),
    )
    check("ACTION festival", decide_play(gs, "t1"), "ACTION festival")
    check("BUY gold", decide_play(gs, "t1"), "BUY gold")

    end_game_state("bad")
    init_game("bad")
    reset_turn("bad")
    check(
        "crash safe END_TURN",
        decide_play(make_game({CardName.COPPER: 1}), "bad")
        in ("END_TURN", "BUY silver", "BUY chapel"),
        True,
    )

    hand_attacked = [CardName.GOLD, CardName.CURSE, CardName.ESTATE, CardName.COPPER]
    check("discard curse", choose_discard(hand_attacked), CardName.CURSE)
    check("confirm discard curse", confirm_discard(CardName.CURSE, hand_attacked), True)
    check("confirm trash copper", confirm_trash(CardName.COPPER, hand_attacked, mem), True)
    check(
        "trash curse first",
        choose_trash([CardName.SILVER, CardName.CURSE, CardName.COPPER], mem),
        CardName.CURSE,
    )
    check(
        "gain witch si dispo",
        choose_gain([CardName.SILVER, CardName.WITCH, CardName.COPPER], mem),
        CardName.WITCH,
    )
    check(
        "skip curse reception",
        skip_reception(CardName.CURSE, [CardName.GOLD]),
        True,
    )
    check(
        "mine upgrade copper",
        choose_money_to_upgrade([CardName.SILVER, CardName.COPPER]),
        CardName.COPPER,
    )

    print("Tous les tests OK.")


if __name__ == "__main__":
    main()
