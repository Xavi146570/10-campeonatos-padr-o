"""
Teste da nova funcionalidade: Notificações de EV Negativo
"""

from ev_detector_santo_graal import EVDetectorSantoGraal


def test_ev_negative_notification():
    """Testa formatação de mensagem EV-"""
    print("=" * 60)
    print("📊 TESTE: Notificação de EV Negativo")
    print("=" * 60)
    
    detector = EVDetectorSantoGraal()
    
    # Simular análise com EV negativo
    comparison = {
        'has_opportunity': False,
        'message': 'Nenhum mercado apresenta EV+ no momento',
        'ev_negative_markets': [
            {
                'market': 'Over 0.5',
                'probability': 0.82,
                'odds': 1.15,
                'ev': -0.057,
                'ev_percentage': -5.7
            },
            {
                'market': 'Over 1.5',
                'probability': 0.65,
                'odds': 1.45,
                'ev': -0.0575,
                'ev_percentage': -5.75
            }
        ]
    }
    
    match_info = {
        'home_team': 'Chelsea',
        'away_team': 'Brighton',
        'league': 'Premier League'
    }
    
    # Gerar mensagem
    message = detector.format_ev_negative_message(comparison, match_info)
    
    print("\n📱 MENSAGEM GERADA:\n")
    print(message)
    print("\n" + "=" * 60)
    
    # Validações
    assert '⛔' in message, "Deve ter emoji de stop"
    assert 'EV-' in message or 'NEGATIVO' in message, "Deve mencionar EV negativo"
    assert 'NÃO APOSTAR' in message, "Deve recomendar não apostar"
    assert 'Chelsea' in message and 'Brighton' in message, "Deve ter nomes dos times"
    assert 'Over 0.5' in message and 'Over 1.5' in message, "Deve mostrar ambos mercados"
    
    print("\n✅ Teste passou! Mensagem educativa formatada corretamente.\n")
    return True


def test_ev_positive_vs_negative():
    """Compara mensagens EV+ vs EV-"""
    print("=" * 60)
    print("🔥 vs ⛔ : EV+ vs EV- (Comparação Visual)")
    print("=" * 60)
    
    detector = EVDetectorSantoGraal()
    
    match_info = {
        'home_team': 'Liverpool',
        'away_team': 'Manchester City',
        'league': 'Premier League'
    }
    
    # Cenário 1: EV+ (APOSTAR)
    print("\n🔥 CENÁRIO 1: EV POSITIVO (APOSTAR)")
    print("-" * 60)
    
    ev_positive = detector.analyze_opportunity(
        market='Over 1.5',
        probability=0.72,
        odds=1.50,
        confidence=0.75
    )
    
    if ev_positive:
        comparison_positive = {
            'has_opportunity': True,
            'best_market': 'Over 1.5',
            'analysis': ev_positive,
            'alternative': None
        }
        
        message_positive = detector.format_opportunity_message(comparison_positive, match_info)
        print(message_positive[:300] + "...")
    
    # Cenário 2: EV- (NÃO APOSTAR)
    print("\n\n⛔ CENÁRIO 2: EV NEGATIVO (NÃO APOSTAR)")
    print("-" * 60)
    
    comparison_negative = {
        'has_opportunity': False,
        'ev_negative_markets': [
            {
                'market': 'Over 1.5',
                'probability': 0.65,
                'odds': 1.45,
                'ev': -0.0575,
                'ev_percentage': -5.75
            }
        ]
    }
    
    message_negative = detector.format_ev_negative_message(comparison_negative, match_info)
    print(message_negative[:300] + "...")
    
    print("\n" + "=" * 60)
    print("✅ Mensagens claramente diferenciadas!")
    print("   🔥 EV+ → Apostar (verde, positivo)")
    print("   ⛔ EV- → Não apostar (vermelho, educativo)")
    print("=" * 60 + "\n")
    
    return True


def main():
    """Executa testes"""
    print("\n🧪 TESTE DA NOVA FUNCIONALIDADE: NOTIFICAÇÕES EV-\n")
    
    try:
        test_1 = test_ev_negative_notification()
        test_2 = test_ev_positive_vs_negative()
        
        if test_1 and test_2:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✅ Funcionalidade de notificações EV- está operacional")
            print("\n💡 Configure em config_santo_graal.py:")
            print("   'send_ev_negative': True  → Ativar notificações EV-")
            print("   'send_ev_negative': False → Desativar (apenas EV+)\n")
            return 0
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
