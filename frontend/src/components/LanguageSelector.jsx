import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import BrasilFlag from 'src/assets/icons/flags/BrasilFlag';
import EEUUFlag from 'src/assets/icons/flags/EEUUFlag';
import ESFlag from 'src/assets/icons/flags/ESFlag';

const LanguageSelector = () => {
    const { i18n } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    const languages = [
        {
            code: 'es',
            name: 'Español',
            flag: ESFlag,
            short: 'ES'
        },
        {
            code: 'en',
            name: 'English',
            flag: EEUUFlag,
            short: 'EN'
        },
        {
            code: 'pt',
            name: 'Português',
            flag: BrasilFlag,
            short: 'PT'
        }
    ];

    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

    const handleLanguageChange = (languageCode) => {
        i18n.changeLanguage(languageCode);
        setIsOpen(false);
        localStorage.setItem('preferred-language', languageCode);
    };

    // Cerrar dropdown al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="group flex items-center gap-2 px-3 py-2 text-sm font-medium text-aloja-gray-700 hover:text-aloja-navy hover:bg-gray-50 rounded-lg transition-all duration-200 border border-transparent hover:border-gray-200"
            >
                <div className="w-6 h-4 rounded-sm shadow-sm overflow-hidden">
                    <currentLanguage.flag size="24px" className="w-full h-full" />
                </div>
                <span className="hidden sm:inline font-medium">{currentLanguage.name}</span>
                <span className="sm:hidden font-semibold text-xs">{currentLanguage.short}</span>
                <svg
                    className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden animate-in slide-in-from-top-2 duration-200">
                    <div className="py-1">
                        {languages.map((language, index) => (
                            <button
                                key={language.code}
                                onClick={() => handleLanguageChange(language.code)}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 group ${language.code === i18n.language
                                        ? 'bg-gradient-to-r from-aloja-blue-50 to-blue-100 text-aloja-navy font-semibold'
                                        : 'text-gray-700 hover:text-aloja-navy'
                                    } ${index === 0 ? 'rounded-t-lg' : ''} ${index === languages.length - 1 ? 'rounded-b-lg' : ''}`}
                            >
                                <div className="w-6 h-4 rounded-sm shadow-sm overflow-hidden group-hover:scale-110 transition-transform duration-200">
                                    <language.flag size="24px" className="w-full h-full" />
                                </div>
                                <div className="flex-1">
                                    <div className="font-medium">{language.name}</div>
                                    <div className="text-xs text-gray-500 uppercase tracking-wide">{language.short}</div>
                                </div>
                                {language.code === i18n.language && (
                                    <svg className="w-4 h-4 text-aloja-navy animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default LanguageSelector;
