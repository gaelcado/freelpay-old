import { TranslationKey } from '@/hooks/useTranslation'

type TranslationFunction = (key: TranslationKey | string) => string;

export const getStatusText = (status: string, t: TranslationFunction) => {
  switch (status) {
    case 'A': return t('common.sirenValidation.companyDetails.statuses.active');
    case 'C': return t('common.sirenValidation.companyDetails.statuses.ceased');
    default: return t('common.sirenValidation.companyDetails.statuses.unknown');
  }
};

export const getStaffCategory = (category: string) => {
  const categories: Record<string, string> = {
    '00': '0 salarié',
    '01': '1 ou 2 salariés',
    '02': '3 à 5 salariés',
    '03': '6 à 9 salariés',
    '11': '10 à 19 salariés',
    '12': '20 à 49 salariés',
    '21': '50 à 99 salariés',
    '22': '100 à 199 salariés',
    '31': '200 à 249 salariés',
    '32': '250 à 499 salariés',
    '41': '500 à 999 salariés',
    '42': '1 000 à 1 999 salariés',
    '51': '2 000 à 4 999 salariés',
    '52': '5 000 à 9 999 salariés',
    '53': '10 000 salariés et plus',
  };
  return categories[category] || 'Non renseigné';
}; 