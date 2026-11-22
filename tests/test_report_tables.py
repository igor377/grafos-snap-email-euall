from src.report_tables import dec, inteiro, num, sci, tex_text


def test_ptbr_number_formatting():
    assert inteiro(224832) == "224.832"
    assert inteiro(14) == "14"
    assert dec(3.02381, 3) == "3,024"
    assert dec(1234.5, 1) == "1.234,5"
    assert sci(1.0359e-05) == r"$1{,}04\times10^{-5}$"
    assert num(2.66e-05) == r"$2{,}66\times10^{-5}$"
    assert num(0.9065456, 3) == "0,907"


def test_tex_text_escapes_and_formats_integers():
    s = tex_text("matriz 300×300; 224832 vértices; 5% & a_b; entrada≠saída")
    assert r"$\times$" in s and r"\%" in s and r"\&" in s and r"\_" in s and r"$\neq$" in s
    assert "224.832" in s and "300" in s
    assert tex_text("Erdős–Rényi") == r"Erd\H{o}s--Rényi"
