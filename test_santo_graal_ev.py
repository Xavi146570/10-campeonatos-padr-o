"""
Script de Teste para Santo Graal Bot EV+
Valida cálculos matemáticos e detecção de valor
"""

import sys
from probability_calculator_santo_graal import ProbabilityCalculatorSantoGraal
from ev_detector_santo_graal import EVDetectorSantoGraal


def test_probability_calculator():
    """Testa cálculo de probabilidades"""
    print("=" * 60)
    print("🧮 TESTE: Calculador de Probabilidades")
    print("=" * 60)
    
    calculator = ProbabilityCalculatorSantoGraal()
    
    # Dados de teste: jogo equilibrado, times ofensivos
    home_stats = {
        'goals_per_game': 2.0,
        'over_0_5_rate': 0.85,
        'over_1_5_rate': 0.70,
        'recent_over_0_5_rate': 0.80,
        'recent_over_1_5_rate': 0.65,
        'offensive_rating': 65,
        'goals_last_5': 10,
        'games_played': 15,
        'position': 5
    }
    
    away_stats = {
        'goals_per_game': 1.8,
        'over_0_5_rate': 0.82,
        'over_1_5_rate': 0.68,
        'recent_over_0_5_rate': 0.85,
        'recent_over_1_5_rate': 0.70,
        'offensive_rating': 62,
        'goals_last_5': 9,
        'games_played': 15,
        'position': 7
    }
    
    h2h_stats = {
        'total_games': 5,
        'over_0_5_rate': 0.80,
        'over_1_5_rate': 0.60
    }
    
    match_info = {
        'home_team': 'Liverpool',
        'away_team': 'Manchester City',
        'league': 'Premier League',
        'games_played': 15,
        'home_position': 5,
        'away_position': 7,
        'is_derby': False
    }
    
    # Calcular probabilidades
    probabilities = calculator.calculate_probabilities_at_ht(
        home_stats,
        away_stats,
        h2h_stats,
        match_info
    )
    
    print(f"\n📊 Cenário: Liverpool vs Manchester City (HT 0-0)")
    print(f"   Gols esperados 2º tempo: {probabilities['expected_goals_2h']}")
    print(f"\n✅ Probabilidades Calculadas:")
    print(f"   Over 0.5: {probabilities['over_0_5']:.2%}")
    print(f"   Over 1.5: {probabilities['over_1_5']:.2%}")
    print(f"   Confiança: {probabilities['confidence']:.2%}")
    
    # Validações
    assert 0.70 <= probabilities['over_0_5'] <= 0.95, "Over 0.5 fora do esperado"
    assert 0.60 <= probabilities['over_1_5'] <= 0.85, "Over 1.5 fora do esperado"
    assert probabilities['over_0_5'] > probabilities['over_1_5'], "Over 0.5 deve ser > Over 1.5"
    
    print(f"\n✅ Todos os testes de probabilidade passaram!")
    return True


def test_ev_detector():
    """Testa detector de Expected Value"""
    print("\n" + "=" * 60)
    print("💰 TESTE: Detector de Expected Value")
    print("=" * 60)
    
    detector = EVDetectorSantoGraal()
    
    # Teste 1: EV+ claro
    print(f"\n📌 TESTE 1: EV+ claro (probabilidade alta, odd boa)")
    analysis_1 = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.72,  # 72%
        odds=1.50,
        confidence=0.75
    )
    
    if analysis_1:
        print(f"   ✅ EV detectado: +{analysis_1['ev_percentage']:.2f}%")
        print(f"   Stake recomendado: {analysis_1['recommended_stake']:.2f}%")
        assert analysis_1['ev_percentage'] > 5.0, "EV deve ser > 5%"
    else:
        print(f"   ❌ ERRO: Deveria detectar EV+")
        return False
    
    # Teste 2: EV- (não deve detectar)
    print(f"\n📌 TESTE 2: EV- (probabilidade baixa)")
    analysis_2 = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.55,  # 55%
        odds=1.50,
        confidence=0.75
    )
    
    if analysis_2 is None:
        print(f"   ✅ Corretamente rejeitado (EV negativo)")
    else:
        print(f"   ❌ ERRO: Não deveria detectar esta oportunidade")
        return False
    
    # Teste 3: EV marginal (~5%)
    print(f"\n📌 TESTE 3: EV no limite (+5%)")
    analysis_3 = detector.analyze_opportunity(
        market='Over 0.5',
        probability=0.88,  # 88%
        odds=1.20,
        confidence=0.80
    )
    
    if analysis_3:
        print(f"   ✅ EV detectado: +{analysis_3['ev_percentage']:.2f}%")
        assert 5.0 <= analysis_3['ev_percentage'] <= 10.0, "EV fora do esperado"
    else:
        print(f"   ⚠️  No limite, pode ou não detectar")
    
    # Teste 4: Comparação de mercados
    print(f"\n📌 TESTE 4: Comparação Over 0.5 vs Over 1.5")
    
    over_0_5 = detector.analyze_opportunity(
        market='Over 0.5',
        probability=0.85,
        odds=1.18,
        confidence=0.78
    )
    
    over_1_5 = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.70,
        odds=1.52,
        confidence=0.75
    )
    
    comparison = detector.compare_markets(over_0_5, over_1_5)
    
    if comparison.get('has_opportunity'):
        print(f"   ✅ Melhor mercado: {comparison['best_market']}")
        print(f"   EV: +{comparison['analysis']['ev_percentage']:.2f}%")
        
        if comparison.get('alternative'):
            print(f"   Alternativa: {comparison['alternative']['market']}")
            print(f"   EV alternativa: +{comparison['alternative']['analysis']['ev_percentage']:.2f}%")
    else:
        print(f"   ❌ ERRO: Deveria detectar pelo menos uma oportunidade")
        return False
    
    print(f"\n✅ Todos os testes de EV passaram!")
    return True


def test_kelly_criterion():
    """Testa cálculo de Kelly"""
    print("\n" + "=" * 60)
    print("📐 TESTE: Kelly Criterion")
    print("=" * 60)
    
    detector = EVDetectorSantoGraal()
    
    # Cenários de teste
    scenarios = [
        {
            'name': 'Alto valor, alta probabilidade',
            'probability': 0.75,
            'odds': 1.60,
            'expected_kelly': 33.0  # Kelly = ((0.6*0.75) - 0.25) / 0.6 = 33%
        },
        {
            'name': 'Valor moderado, probabilidade média',
            'probability': 0.65,
            'odds': 1.70,
            'expected_kelly': 15.0  # Kelly = ((0.7*0.65) - 0.35) / 0.7 = 15%
        },
        {
            'name': 'Probabilidade muito alta, odds baixas',
            'probability': 0.90,
            'odds': 1.15,
            'expected_kelly': 23.0  # Kelly = ((0.15*0.90) - 0.10) / 0.15 = 23%
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}")
        print(f"   Probabilidade: {scenario['probability']:.0%}")
        print(f"   Odds: {scenario['odds']}")
        
        kelly = detector._calculate_kelly(scenario['probability'], scenario['odds'])
        print(f"   Kelly completo: {kelly:.2f}%")
        
        # Kelly conservador (25%)
        conservative = kelly * detector.kelly_fraction
        print(f"   Kelly conservador (25%): {conservative:.2f}%")
        
        # Validar que está na faixa esperada (±3%)
        tolerance = 3.0
        assert abs(kelly - scenario['expected_kelly']) < tolerance, \
            f"Kelly fora do esperado: {kelly:.2f}% vs {scenario['expected_kelly']:.2f}%"
    
    print(f"\n✅ Todos os testes de Kelly passaram!")
    return True


def test_edge_cases():
    """Testa casos extremos"""
    print("\n" + "=" * 60)
    print("🔬 TESTE: Casos Extremos")
    print("=" * 60)
    
    detector = EVDetectorSantoGraal()
    
    # Caso 1: Odds muito baixas
    print(f"\n📌 Odds muito baixas (1.05)")
    result = detector.analyze_opportunity(
        market='Over 0.5',
        probability=0.95,
        odds=1.05,  # Abaixo do mínimo
        confidence=0.80
    )
    assert result is None, "Deveria rejeitar odds muito baixas"
    print(f"   ✅ Corretamente rejeitado")
    
    # Caso 2: Odds muito altas
    print(f"\n📌 Odds muito altas (3.50)")
    result = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.60,
        odds=3.50,  # Acima do máximo
        confidence=0.70
    )
    assert result is None, "Deveria rejeitar odds muito altas"
    print(f"   ✅ Corretamente rejeitado")
    
    # Caso 3: Probabilidade muito baixa
    print(f"\n📌 Probabilidade muito baixa (40%)")
    result = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.40,  # Abaixo do mínimo
        odds=2.00,
        confidence=0.75
    )
    assert result is None, "Deveria rejeitar probabilidade muito baixa"
    print(f"   ✅ Corretamente rejeitado")
    
    # Caso 4: Confiança baixa ajusta stake
    print(f"\n📌 Confiança baixa (50%)")
    result = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.70,
        odds=1.60,
        confidence=0.50  # Baixa confiança
    )
    if result:
        print(f"   ✅ Detectado, mas stake ajustado: {result['recommended_stake']:.2f}%")
        assert result['recommended_stake'] < 3.0, "Stake deveria ser baixo com confiança baixa"
    else:
        print(f"   ⚠️  Rejeitado por confiança muito baixa")
    
    print(f"\n✅ Todos os testes de casos extremos passaram!")
    return True


def main():
    """Executa todos os testes"""
    print("\n" + "🧪" * 30)
    print("SUITE DE TESTES - SANTO GRAAL BOT EV+")
    print("🧪" * 30 + "\n")
    
    try:
        # Executar testes
        test_1 = test_probability_calculator()
        test_2 = test_ev_detector()
        test_3 = test_kelly_criterion()
        test_4 = test_edge_cases()
        
        # Resumo
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"✅ Calculador de Probabilidades: {'PASSOU' if test_1 else 'FALHOU'}")
        print(f"✅ Detector de EV: {'PASSOU' if test_2 else 'FALHOU'}")
        print(f"✅ Kelly Criterion: {'PASSOU' if test_3 else 'FALHOU'}")
        print(f"✅ Casos Extremos: {'PASSOU' if test_4 else 'FALHOU'}")
        
        if all([test_1, test_2, test_3, test_4]):
            print("\n" + "🎉" * 30)
            print("TODOS OS TESTES PASSARAM COM SUCESSO!")
            print("Sistema pronto para uso!")
            print("🎉" * 30 + "\n")
            return 0
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
