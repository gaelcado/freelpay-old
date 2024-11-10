import api from '@/lib/api';
import { translations } from '@/lib/translations'

type TranslationsType = typeof translations.en
type TranslationFunction = (key: keyof typeof translations.en | `${keyof typeof translations.en}.${string}`) => string;

export interface CompanyInfo {
  siren: string;
  name: string;
  address: string;
  activity?: string;
  creation_date?: string;
  category?: string;
  staff_category?: string;
  staff_year?: number;
  company_category?: string;
  legal_category?: string;
  social_economy?: string;
  employer?: string;
  status?: string;
}

interface SirenResponse {
  unite_legale: {
    siren: string;
    denomination: string;
    activite_principale?: string;
    date_creation?: string;
    etablissement_siege: {
      geo_adresse: string;
    };
    categorie_entreprise?: string;
    tranche_effectifs?: string;
    annee_effectifs?: number;
    categorie_juridique?: string;
    economie_sociale_solidaire?: string;
    caractere_employeur?: string;
    etat_administratif?: string;
  };
}

export const validateSiren = async (siren: string, t: TranslationFunction): Promise<CompanyInfo> => {
  try {
    const response = await api.get<SirenResponse>(`/api/siren/validate/${siren}`);
    const ul = response.data.unite_legale;
    
    return {
      siren: ul.siren,
      name: ul.denomination,
      address: ul.etablissement_siege.geo_adresse,
      activity: ul.activite_principale,
      creation_date: ul.date_creation,
      category: ul.categorie_entreprise,
      staff_category: ul.tranche_effectifs,
      staff_year: ul.annee_effectifs,
      company_category: ul.categorie_entreprise,
      legal_category: ul.categorie_juridique,
      social_economy: ul.economie_sociale_solidaire,
      employer: ul.caractere_employeur,
      status: ul.etat_administratif
    };
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error(t('common.sirenValidation.invalidSiren'));
    }
    if (error.response?.status === 400) {
      throw new Error(t('common.sirenValidation.incorrectFormat'));
    }
    throw new Error(t('common.sirenValidation.verificationError'));
  }
}; 