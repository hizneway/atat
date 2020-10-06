from script.generate_under_maintenance import file_is_too_large, main


def test_generate_under_maintence_page(tmp_path):
    main(tmp_path)
    assert not file_is_too_large(tmp_path / "index.html")
