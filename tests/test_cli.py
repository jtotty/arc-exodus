from arc_exodus.cli import create_parser


class TestCreateParser:
    def test_creates_parser_with_program_name(self) -> None:
        parser = create_parser()
        assert parser.prog == "arc-exodus"

    def test_creates_parser_with_description(self) -> None:
        parser = create_parser()
        assert parser.description is not None
