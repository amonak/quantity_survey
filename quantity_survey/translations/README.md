# Quantity Survey Translations

This directory contains translation files for the Quantity Survey application.

## Supported Languages:

### English (en)
- en.csv - English translations (base language)

### French (fr)
- fr.csv - French translations

### Spanish (es)
- es.csv - Spanish translations

### German (de)
- de.csv - German translations

### Portuguese (pt)
- pt.csv - Portuguese translations

### Arabic (ar)
- ar.csv - Arabic translations

## File Format:
Translation files use CSV format with columns:
- Source Text (English)
- Translated Text (Target Language)
- Context (Optional)

Example:
```csv
"Bill of Quantities","Facture des Quantités",""
"Valuation","Évaluation",""
"Payment Certificate","Certificat de Paiement",""
```

## Usage:
Translations are automatically loaded by Melon framework.
Use `_(...)` function in Python and `__('...')` in JavaScript for translatable strings.

## Adding New Languages:
1. Create new CSV file with language code (e.g., it.csv for Italian)
2. Add all translatable strings from the application
3. Provide translations for each string
4. Update language list in app configuration

## Translation Guidelines:
- Keep technical terms consistent
- Consider cultural context
- Maintain proper capitalization
- Test translations in UI context
- Use standard construction terminology
