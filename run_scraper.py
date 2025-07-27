#!/usr/bin/env python3
"""
Executa o scraper principal
"""

from futbin_mass_scraper import FutbinMassScraper

def main():
    """Executa o scraper"""
    
    print("🚀 INICIANDO SCRAPER FUTBIN")
    print("=" * 50)
    
    # Criar scraper (token será obtido das variáveis de ambiente)
    scraper = FutbinMassScraper()
    
    # Executar scraping em massa
    scraper.run_mass_scraping()

if __name__ == "__main__":
    main() 