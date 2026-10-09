import streamlit as st
import streamlit.components.v1 as components
import easyocr
import urllib.request
import urllib.parse
import urllib.error
import time
import random
from PIL import Image, ImageOps
import numpy as np
import json
import re
import gspread
from gspread.exceptions import APIError
import pandas as pd
from datetime import datetime
import base64
import io
import uuid

st.set_page_config(page_title="Fransızca Storybook / Lycée Français", layout="wide")

# ==========================================
# 0. KAPSAMLI ÇOKLU DİL SÖZLÜĞÜ (I18N)
# ==========================================
LANGUAGES = {
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "tr": {"name": "Türkçe", "flag": "🇹🇷"},
    "en": {"name": "English", "flag": "🇬🇧"},
    "bg": {"name": "Български", "flag": "🇧🇬"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "ar": {"name": "العربية", "flag": "🇸🇦"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "it": {"name": "Italiano", "flag": "🇮🇹"},
    "ru": {"name": "Русский", "flag": "🇷🇺"},
}

I18N = {
    "title": {
        "fr": "📚 Compagnon de Lecture - Lycée Victor Hugo",
        "tr": "📚 Fransızca Çocuk Kitabı Okuma Arkadaşı",
        "en": "📚 French Storybook Reading Companion",
        "bg": "📚 Четец за френски детски приказки",
        "de": "📚 Französischer Lese- und Übersetzungsbegleiter",
        "ar": "📚 رفيق قراءة وترجمة القصص الفرنسية للأطفال",
        "es": "📚 Compañero de Lectura de Cuentos en Francés",
        "it": "📚 Compagno di Lettura di Fiabe in Francese",
        "ru": "📚 Помощник для чтения французских сказок",
    },
    "tab_read": {
        "fr": "📖 Lecture & Traduction", "tr": "📖 Okuma & Çeviri", "en": "📖 Reading & Translation",
        "bg": "📖 Четене & Превод", "de": "📖 Lesen & Übersetzung", "ar": "📖 القراءة والترجمة",
        "es": "📖 Lectura y Traducción", "it": "📖 Lettura e Traduzione", "ru": "📖 Чтение и перевод"
    },
    "tab_my_lib": {
        "fr": "📚 Ma Bibliothèque", "tr": "📚 Kütüphanem", "en": "📚 My Library",
        "bg": "📚 Моята библиотека", "de": "📚 Meine Bibliothek", "ar": "📚 مكتبتي",
        "es": "📚 Mi Biblioteca", "it": "📚 La Mia Libreria", "ru": "📚 Моя библиотека"
    },
    "tab_community": {
        "fr": "🌍 Bibliothèque Scolaire", "tr": "🌍 Ortak Kütüphane", "en": "🌍 School Library",
        "bg": "🌍 Училищна библиотека", "de": "🌍 Schulbibliothek", "ar": "🌍 مكتبة المدرسة المشتركة",
        "es": "🌍 Biblioteca Escolar", "it": "🌍 Libreria Scolastica", "ru": "🌍 Школьная библиотека"
    },
    "tab_admin": {
        "fr": "👑 Administration", "tr": "👑 Yönetici Paneli", "en": "👑 Admin Panel",
        "bg": "👑 Администрация", "de": "👑 Admin-Bereich", "ar": "👑 لوحة الإدارة",
        "es": "👑 Panel de Administración", "it": "👑 Pannello Admin", "ru": "👑 Панель управления"
    },
    "prev_page": {
        "fr": "⬅️ Page précédente", "tr": "⬅️ Önceki Sayfa", "en": "⬅️ Previous Page",
        "bg": "⬅️ Предишна страница", "de": "⬅️ Vorherige Seite", "ar": "⬅️ الصفحة السابقة",
        "es": "⬅️ Página anterior", "it": "⬅️ Pagina precedente", "ru": "⬅️ Предыдущая страница"
    },
    "next_page": {
        "fr": "Page suivante ➡️", "tr": "Sonraki Sayfa ➡️", "en": "Next Page ➡️",
        "bg": "Следваща страница ➡️", "de": "Nächste Seite ➡️", "ar": "الصفحة التالية ➡️",
        "es": "Página siguiente ➡️", "it": "Pagina successiva ➡️", "ru": "Следующая страница ➡️"
    },
    "page_label": {
        "fr": "Page", "tr": "Sayfa", "en": "Page", "bg": "Страница",
        "de": "Seite", "ar": "صفحة", "es": "Página", "it": "Pagina", "ru": "Страница"
    },
    "step1_title": {
        "fr": "Étape 1 : Importer les pages du livre", "tr": "1. Adım: Kitap Sayfalarını Yükleyin",
        "en": "Step 1: Upload Book Pages", "bg": "Стъпка 1: Качете страниците на книгата",
        "de": "Schritt 1: Buchseiten hochladen", "ar": "الخطوة 1: تحميل صفحات الكتاب",
        "es": "Paso 1: Subir páginas del libro", "it": "Passo 1: Carica le pagine del libro", "ru": "Шаг 1: Загрузите страницы книги"
    },
    "step1_uploader": {
        "fr": "Sélectionnez toutes les photos", "tr": "Tüm fotoğrafları seçin",
        "en": "Select all photos", "bg": "Изберете всички снимки",
        "de": "Alle Fotos auswählen", "ar": "حدد جميع الصور",
        "es": "Selecciona todas las fotos", "it": "Seleziona tutte le foto", "ru": "Выберите все фотографии"
    },
    "step1_btn": {
        "fr": "Continuer (Organiser les pages) ➡️", "tr": "Devam Et (Sayfaları Düzenle) ➡️",
        "en": "Continue (Arrange Pages) ➡️", "bg": "Продължи (Подреди страниците) ➡️",
        "de": "Weiter (Seiten anordnen) ➡️", "ar": "متابعة (ترتيب الصفحات) ➡️",
        "es": "Continuar (Organizar páginas) ➡️", "it": "Continua (Ordina pagine) ➡️", "ru": "Продолжить (Упорядочить страницы) ➡️"
    },
    "step2_title": {
        "fr": "Étape 2 : Organiser l'ordre des pages", "tr": "2. Adım: Sayfa Sıralamasını Düzenleyin",
        "en": "Step 2: Arrange Page Order", "bg": "Стъпка 2: Подреждане на реда на страниците",
        "de": "Schritt 2: Seitenreihenfolge anordnen", "ar": "الخطوة 2: ترتيب تسلسل الصفحات",
        "es": "Paso 2: Organizar el orden de las páginas", "it": "Passo 2: Ordina le pagine", "ru": "Шаг 2: Настройте порядок страниц"
    },
    "step2_desc": {
        "fr": "Utilisez les flèches pour modifier l'ordre si nécessaire ou supprimez les pages erronées.",
        "tr": "Sıralama yanlışsa yön tuşlarıyla düzeltebilir veya hatalı sayfayı silebilirsiniz.",
        "en": "Use arrows to adjust the order if needed, or remove unwanted pages.",
        "bg": "Използвайте стрелките, за да промените реда, или изтрийте грешните страници.",
        "de": "Verwenden Sie die Pfeile, um die Reihenfolge anzupassen, oder löschen Sie Seiten.",
        "ar": "استخدم الأسهم لتعديل الترتيب إذا لزم الأمر أو احذف الصفحات غير المرغوبة.",
        "es": "Usa las flechas para ajustar el orden o elimina páginas no deseadas.",
        "it": "Usa le frecce per modificare l'ordine o elimina le pagine errate.",
        "ru": "Используйте стрелки для изменения порядка или удалите ненужные страницы."
    },
    "step2_back": {
        "fr": "⬅️ Retour (Téléverser à nouveau)", "tr": "⬅️ Geri (Tekrar Yükle)",
        "en": "⬅️ Back (Re-upload)", "bg": "⬅️ Назад (Качи отново)",
        "de": "⬅️ Zurück (Erneut hochladen)", "ar": "⬅️ رجوع (إعادة التحميل)",
        "es": "⬅️ Volver (Volver a subir)", "it": "⬅️ Indietro (Ricarica)", "ru": "⬅️ Назад (Загрузить снова)"
    },
    "step2_done": {
        "fr": "✅ Ordre confirmé, Commencer la lecture", "tr": "✅ Sıralama Tamam, Okumaya Başla",
        "en": "✅ Order Confirmed, Start Reading", "bg": "✅ Редът е потвърден, Започни четене",
        "de": "✅ Reihenfolge bestätigt, Lesen starten", "ar": "✅ تم تأكيد الترتيب، ابدأ القراءة",
        "es": "✅ Orden confirmado, Empezar a leer", "it": "✅ Ordine confermato, Inizia a leggere", "ru": "✅ Порядок подтвержден, начать чтение"
    },
    "open_book_info": {
        "fr": "📘 Livre ouvert :", "tr": "📘 Açık Kitap:", "en": "📘 Current Book:",
        "bg": "📘 Отворена книга:", "de": "📘 Geöffnetes Buch:", "ar": "📘 الكتاب المفتوح:",
        "es": "📘 Libro abierto:", "it": "📘 Libro aperto:", "ru": "📘 Открытая книга:"
    },
    "close_book": {
        "fr": "❌ Fermer ce livre (Nouveau livre)", "tr": "❌ Bu Kitabı Kapat (Yeni Kitap Yükle)",
        "en": "❌ Close book (Upload new)", "bg": "❌ Затвори тази книга (Качи нова)",
        "de": "❌ Buch schließen (Neues Buch)", "ar": "❌ إغلاق هذا الكتاب (تحميل جديد)",
        "es": "❌ Cerrar este libro (Subir nuevo)", "it": "❌ Chiudi questo libro (Carica nuovo)", "ru": "❌ Закрыть книгу (Загрузить новую)"
    },
    "orientation": {
        "fr": "Orientation :", "tr": "Yönlendirme:", "en": "Orientation:",
        "bg": "Ориентация:", "de": "Ausrichtung:", "ar": "الاتجاه:",
        "es": "Orientación:", "it": "Orientamento:", "ru": "Ориентация:"
    },
    "save_header": {
        "fr": "💾 Enregistrer ce livre dans la bibliothèque", "tr": "💾 Bu Kitabı Kütüphaneye Kaydet",
        "en": "💾 Save this book to library", "bg": "💾 Запази тази книга в библиотеката",
        "de": "💾 Dieses Buch speichern", "ar": "💾 حفظ هذا الكتاب في المكتبة",
        "es": "💾 Guardar este libro en la biblioteca", "it": "💾 Salva questo libro nella libreria", "ru": "💾 Сохранить эту книгу в библиотеку"
    },
    "book_name": {
        "fr": "Titre du livre :", "tr": "Kitap İsmi:", "en": "Book Title:",
        "bg": "Заглавие на книгата:", "de": "Buchtitel:", "ar": "اسم الكتاب:",
        "es": "Título del libro:", "it": "Titolo del libro:", "ru": "Название книги:"
    },
    "share_opt": {
        "fr": "🌍 Partager avec les autres familles (Bibliothèque Scolaire)",
        "tr": "🌍 Diğer velilerle de paylaş (Ortak Kütüphane)",
        "en": "🌍 Share with other families (School Library)",
        "bg": "🌍 Сподели с останалите семейства (Училищна библиотека)",
        "de": "🌍 Mit anderen Familien teilen (Schulbibliothek)",
        "ar": "🌍 مشاركة مع العائلات الأخرى (مكتبة المدرسة)",
        "es": "🌍 Compartir con las demás familias (Biblioteca Escolar)",
        "it": "🌍 Condividi con le altre famiglie (Libreria Scolastica)",
        "ru": "🌍 Поделиться с другими семьями (Школьная библиотека)"
    },
    "btn_save": {
        "fr": "💾 Enregistrer dans le Cloud", "tr": "💾 Kitabı Buluta Kaydet", "en": "💾 Save Book to Cloud",
        "bg": "💾 Запази в облака", "de": "💾 In der Cloud speichern", "ar": "💾 حفظ في السحابة",
        "es": "💾 Guardar en la Nube", "it": "💾 Salva nel Cloud", "ru": "💾 Сохранить в облаке"
    },
    "login_to_save": {
        "fr": "⚠️ Veuillez vous connecter pour enregistrer ce livre.",
        "tr": "⚠️ Kitabı kaydetmek için lütfen sol menüden giriş yapın.",
        "en": "⚠️ Please log in to save this book.",
        "bg": "⚠️ Моля, влезте в профила си, за да запазите тази книга.",
        "de": "⚠️ Bitte melden Sie sich an, um dieses Buch zu speichern.",
        "ar": "⚠️ يرجى تسجيل الدخول لحفظ هذا الكتاب.",
        "es": "⚠️ Inicia sesión para guardar este libro.",
        "it": "⚠️ Accedi per salvare questo libro.",
        "ru": "⚠️ Пожалуйста, войдите, чтобы сохранить эту книгу."
    },
    "ocr_header": {
        "fr": "🎤 Karaoké interactif & Traduction", "tr": "🎤 İnteraktif Karaoke ve Çeviri",
        "en": "🎤 Interactive Karaoke & Translation", "bg": "🎤 Интерактивно караоке и превод",
        "de": "🎤 Interaktives Karaoke & Übersetzung", "ar": "🎤 كاريوكي تفاعلي وترجمة",
        "es": "🎤 Karaoke interactivo y traducción", "it": "🎤 Karaoke interattivo e traduzione", "ru": "🎤 Интерактивное караоке и перевод"
    },
    "edit_prompt": {
        "fr": "Modifier le texte si nécessaire :", "tr": "Düzeltmek isterseniz metni düzenleyin:",
        "en": "Edit text if needed:", "bg": "Редактирайте текста при нужда:",
        "de": "Text bei Bedarf anpassen:", "ar": "قم بتعديل النص إذا لزم الأمر:",
        "es": "Edita el texto si es necesario:", "it": "Modifica il testo se necessario:", "ru": "Отредактируйте текст при необходимости:"
    },
    "btn_translate": {
        "fr": "📝 Traduire tout le texte", "tr": "📝 Tüm Metni Çevir", "en": "📝 Translate Full Text",
        "bg": "📝 Преведи целия текст", "de": "📝 Gesamten Text übersetzen", "ar": "📝 ترجمة النص كاملاً",
        "es": "📝 Traducir todo el texto", "it": "📝 Traduci l'intero testo", "ru": "📝 Перевести весь текст"
    },
    "btn_play": {
        "fr": "▶️ Écouter", "tr": "▶️ Sesli Oku", "en": "▶️ Read Aloud", "bg": "▶️ Прочети",
        "de": "▶️ Vorlesen", "ar": "▶️ قراءة صوتية", "es": "▶️ Leer en voz alta", "it": "▶️ Ascolta", "ru": "▶️ Читать вслух"
    },
    "btn_stop": {
        "fr": "⏹ Arrêter", "tr": "⏹ Durdur", "en": "⏹ Stop", "bg": "⏹ Спри",
        "de": "⏹ Stop", "ar": "⏹ إيقاف", "es": "⏹ Detener", "it": "⏹ Ferma", "ru": "⏹ Стоп"
    },
    "btn_read": {
        "fr": "📖 Lire", "tr": "📖 Oku", "en": "📖 Read", "bg": "📖 Прочети",
        "de": "📖 Lesen", "ar": "📖 قراءة", "es": "📖 Leer", "it": "📖 Leggi", "ru": "📖 Читать"
    },
    "btn_delete": {
        "fr": "🗑️ Supprimer", "tr": "🗑️ Sil", "en": "🗑️ Delete", "bg": "🗑️ Изтрий",
        "de": "🗑️ Löschen", "ar": "🗑️ حذف", "es": "🗑️ Eliminar", "it": "🗑️ Elimina", "ru": "🗑️ Удалить"
    },
    "thank_tolga": {
        "fr": "🙏 Remercier Tolga", "tr": "🙏 Tolga'ya Teşekkür Et", "en": "🙏 Send Thank to Tolga",
        "bg": "🙏 Благодари на Толга", "de": "🙏 Danke an Tolga senden", "ar": "🙏 إرسال شكر إلى تولغا",
        "es": "🙏 Dar las gracias a Tolga", "it": "🙏 Ringrazia Tolga", "ru": "🙏 Поблагодарить Толгу"
    },
    "community_desc": {
        "fr": "Livres partagés par les familles. Vous pouvez les lire sans télécharger de photos.",
        "tr": "Velilerin paylaştığı kitaplar. Tekrar fotoğraf yüklemeden doğrudan okuyabilirsiniz.",
        "en": "Books shared by families. Read directly without uploading photos again.",
        "bg": "Книги, споделени от семействата. Четете директно без повторно качване на снимки.",
        "de": "Von Familien geteilte Bücher. Direkt lesen ohne erneuten Upload.",
        "ar": "كتب تمت مشاركتها من قبل العائلات. اقرأ مباشرة دون إعادة رفع الصور.",
        "es": "Libros compartidos por familias. Léelos directamente sin subir fotos.",
        "it": "Libri condivisi dalle famiglie. Leggi direttamente senza caricare foto.",
        "ru": "Книги, предоставленные семьями. Читайте сразу без повторной загрузки фото."
    },
    "no_books_my": {
        "fr": "Aucun livre enregistré dans votre bibliothèque.",
        "tr": "Henüz kaydettiğiniz bir kitap yok.",
        "en": "No books saved in your library yet.",
        "bg": "Все още нямате запазени книги в библиотеката си.",
        "de": "Noch keine Bücher in Ihrer Bibliothek gespeichert.",
        "ar": "لا توجد كتب محفوظة في مكتبتك حتى الآن.",
        "es": "No tienes libros guardados en tu biblioteca todavía.",
        "it": "Nessun libro salvato nella tua libreria per ora.",
        "ru": "В вашей библиотеке пока нет сохраненных книг."
    },
    "no_books_comm": {
        "fr": "Aucun livre partagé dans la bibliothèque scolaire pour le moment.",
        "tr": "Ortak kütüphanede henüz paylaşılan bir kitap yok.",
        "en": "No shared books in the school library at the moment.",
        "bg": "В момента няма споделени книги в училищната библиотека.",
        "de": "Zurzeit sind keine geteilten Bücher in der Schulbibliothek verfügbar.",
        "ar": "لا توجد كتب مشتركة في مكتبة المدرسة في الوقت الحالي.",
        "es": "No hay libros compartidos en la biblioteca escolar en este momento.",
        "it": "Nessun libro condiviso nella libreria scolastica al momento.",
        "ru": "В школьной библиотеке пока нет общих книг."
    },
    "lib_empty": {
        "fr": "La bibliothèque est vide.", "tr": "Kütüphane henüz boş.", "en": "Library is empty.",
        "bg": "Библиотеката е празна.", "de": "Bibliothek ist leer.", "ar": "المكتبة فارغة.",
        "es": "La biblioteca está vacía.", "it": "La libreria è vuota.", "ru": "Библиотека пуста."
    },
    "login_for_lib": {
        "fr": "Veuillez vous connecter pour accéder à votre bibliothèque personnelle.",
        "tr": "Kendi kütüphanenizi görmek için lütfen sol menüden giriş yapın.",
        "en": "Please log in to view your personal library.",
        "bg": "Моля, влезте в профила си, за да видите личната си библиотека.",
        "de": "Bitte melden Sie sich an, um Ihre persönliche Bibliothek zu sehen.",
        "ar": "يرجى تسجيل الدخول للوصول إلى مكتبتك الشخصية.",
        "es": "Inicia sesión para ver tu biblioteca personal.",
        "it": "Accedi per vedere la tua libreria personale.",
        "ru": "Пожалуйста, войдите, чтобы просмотреть личную библиотеку."
    },
    "status_shared": {
        "fr": "🌍 Partagé (Bibliothèque Scolaire)", "tr": "🌍 Ortak Kütüphanede Açık",
        "en": "🌍 Shared (School Library)", "bg": "🌍 Споделена (Училищна библиотека)",
        "de": "🌍 Geteilt (Schulbibliothek)", "ar": "🌍 مشتركة (مكتبة المدرسة)",
        "es": "🌍 Compartido (Biblioteca Escolar)", "it": "🌍 Condiviso (Libreria Scolastica)", "ru": "🌍 Доступно всем (Школьная библиотека)"
    },
    "status_private": {
        "fr": "🔒 Privé (Visible uniquement par vous)", "tr": "🔒 Sadece Bana Özel",
        "en": "🔒 Private (Only visible to you)", "bg": "🔒 Лична (Вижда се само от вас)",
        "de": "🔒 Privat (Nur für Sie sichtbar)", "ar": "🔒 خاصة (مرئية لك فقط)",
        "es": "🔒 Privado (Solo visible para ti)", "it": "🔒 Privato (Visibile solo da te)", "ru": "🔒 Личное (Видно только вам)"
    },
    "admin_only": {
        "fr": "Accès réservé à l'administrateur.", "tr": "Yalnızca Admin erişebilir.",
        "en": "Access restricted to Administrator.", "bg": "Достъпът е разрешен само за администратор.",
        "de": "Zugriff nur für Administratoren.", "ar": "الوصول مقتصر على المسؤول فقط.",
        "es": "Acceso restringido al Administrador.", "it": "Accesso riservato all'Amministratore.", "ru": "Доступ только для администратора."
    },
    "admin_users": {
        "fr": "👥 Familles inscrites", "tr": "👥 Kayıtlı Veliler", "en": "👥 Registered Families",
        "bg": "👥 Регистрирани семейства", "de": "👥 Registrierte Familien", "ar": "👥 العائلات المسجلة",
        "es": "👥 Familias registradas", "it": "👥 Famiglie registrate", "ru": "👥 Зарегистрированные семьи"
    },
    "admin_thanks": {
        "fr": "🙏 Messages de remerciement reçus", "tr": "🙏 Gelen Teşekkür Mesajları",
        "en": "🙏 Received Thank You Notes", "bg": "🙏 Получени благодарствени съобщения",
        "de": "🙏 Erhaltene Danksagungen", "ar": "🙏 رسائل الشكر المستلمة",
        "es": "🙏 Mensajes de agradecimiento", "it": "🙏 Messaggi di ringraziamento", "ru": "🙏 Полученные благодарности"
    },
    "admin_no_users": {
        "fr": "Aucun utilisateur trouvé.", "tr": "Kullanıcı bulunamadı.", "en": "No users found.",
        "bg": "Няма намерени потребители.", "de": "Keine Benutzer gefunden.", "ar": "لم يتم العثور على مستخدمين.",
        "es": "No se encontraron usuarios.", "it": "Nessun utente trovato.", "ru": "Пользователи не найдены."
    },
    "admin_no_thanks": {
        "fr": "Aucun message pour le moment.", "tr": "Henüz teşekkür mesajı gelmedi.",
        "en": "No thank-you messages yet.", "bg": "Все още няма съобщения.",
        "de": "Noch keine Nachrichten vorhanden.", "ar": "لا توجد رسائل حتى الآن.",
        "es": "Aún no hay mensajes de agradecimiento.", "it": "Ancora nessun messaggio.", "ru": "Пока нет сообщений."
    },
    "sidebar_account": {
        "fr": "👤 Mon Compte", "tr": "👤 Hesabım", "en": "👤 My Account",
        "bg": "👤 Моят профил", "de": "👤 Mein Konto", "ar": "👤 حسابي",
        "es": "👤 Mi Cuenta", "it": "👤 Il Mio Account", "ru": "👤 Мой аккаунт"
    },
    "tab_login": {
        "fr": "Connexion", "tr": "Giriş Yap", "en": "Log In", "bg": "Вход",
        "de": "Anmelden", "ar": "تسجيل الدخول", "es": "Iniciar Sesión", "it": "Accedi", "ru": "Вход"
    },
    "tab_signup": {
        "fr": "S'inscrire", "tr": "Üye Ol", "en": "Sign Up", "bg": "Регистрация",
        "de": "Registrieren", "ar": "إنشاء حساب", "es": "Registrarse", "it": "Registrati", "ru": "Регистрация"
    },
    "email_label": {
        "fr": "E-mail (Confidentiel)", "tr": "E-mail (Gizli)", "en": "Email (Private)",
        "bg": "Имейл (Поверителен)", "de": "E-Mail (Privat)", "ar": "البريد الإلكتروني (خاص)",
        "es": "Correo electrónico (Privado)", "it": "Email (Privata)", "ru": "Эл. почта (Конфиденциально)"
    },
    "nickname_label": {
        "fr": "Pseudo public (Visible par les familles)", "tr": "Görünecek Adınız (Nickname)",
        "en": "Public Nickname (Visible to others)", "bg": "Публичен псевдоним (Видим за всички)",
        "de": "Öffentlicher Nickname", "ar": "الاسم المستعار (مرئي للجميع)",
        "es": "Apodo público", "it": "Nickname pubblico", "ru": "Публичный псевдоним"
    },
    "password_label": {
        "fr": "Mot de passe", "tr": "Şifre", "en": "Password", "bg": "Парола",
        "de": "Passwort", "ar": "كلمة المرور", "es": "Contraseña", "it": "Password", "ru": "Пароль"
    },
    "btn_logout": {
        "fr": "Déconnexion", "tr": "Çıkış Yap", "en": "Log Out", "bg": "Изход",
        "de": "Abmelden", "ar": "تسجيل الخروج", "es": "Cerrar sesión", "it": "Disconnetti", "ru": "Выйти"
    },
    "sidebar_community": {
        "fr": "💌 Communauté", "tr": "💌 Topluluk", "en": "💌 Community",
        "bg": "💌 Общност", "de": "💌 Gemeinschaft", "ar": "💌 المجتمع",
        "es": "💌 Comunidad", "it": "💌 Comunità", "ru": "💌 Сообщество"
    },
    "welcome_msg": {
        "fr": "Bienvenue", "tr": "Hoş geldiniz", "en": "Welcome", "bg": "Добре дошли",
        "de": "Willkommen", "ar": "أهلاً بك", "es": "Bienvenido", "it": "Benvenuto", "ru": "Добро пожаловать"
    },
    "invalid_creds": {
        "fr": "Identifiants invalides !", "tr": "Hatalı E-mail veya Şifre!", "en": "Invalid credentials!",
        "bg": "Невалиден имейл или парола!", "de": "Ungültige Anmeldedaten!", "ar": "بيانات الدخول غير صحيحة!",
        "es": "¡Credenciales no válidas!", "it": "Credenziali non valide!", "ru": "Неверный логин или пароль!"
    },
    "email_exists": {
        "fr": "Cet e-mail est déjà enregistré !", "tr": "Bu e-mail zaten kayıtlı!",
        "en": "This email is already registered!", "bg": "Този имейл вече е регистриран!",
        "de": "Diese E-Mail ist bereits registriert!", "ar": "هذا البريد مسجل بالفعل!",
        "es": "¡Este correo ya está registrado!", "it": "Questa email è già registrata!", "ru": "Этот email уже зарегистрирован!"
    },
    "signup_success": {
        "fr": "Compte créé avec succès ! Connectez-vous.", "tr": "Kayıt başarılı! Giriş yapabilirsiniz.",
        "en": "Account created! Please log in.", "bg": "Профилът е създаден успешно! Моля, влезте.",
        "de": "Konto erstellt! Bitte anmelden.", "ar": "تم إنشاء الحساب بنجاح! يرجى تسجيل الدخول.",
        "es": "¡Cuenta creada! Por favor inicia sesión.", "it": "Account creato! Effettua il login.", "ru": "Аккаунт создан! Пожалуйста, войдите."
    },
    "fill_all_fields": {
        "fr": "Veuillez remplir tous les champs.", "tr": "Lütfen tüm alanları doldurun.",
        "en": "Please fill all fields.", "bg": "Моля, попълнете всички полета.",
        "de": "Bitte alle Felder ausfüllen.", "ar": "يرجى ملء جميع الحقول.",
        "es": "Por favor completa todos los campos.", "it": "Si prega di compilare tutti i campi.", "ru": "Пожалуйста, заполните все поля."
    },
    "toast_thank": {
        "fr": "Votre remerciement a été transmis à Tolga !",
        "tr": "Teşekkür mesajınız Tolga'ya iletildi!",
        "en": "Your thank-you message has been sent to Tolga!",
        "bg": "Вашата благодарност беше изпратена на Толга!",
        "de": "Ihr Dankeschön wurde an Tolga weitergeleitet!",
        "ar": "تم إرسال رسالة الشكر الخاصة بك إلى تولغا!",
        "es": "¡Tu agradecimiento ha sido enviado a Tolga!",
        "it": "Il tuo ringraziamento è stato inviato a Tolga!",
        "ru": "Ваша благодарность передана Толге!"
    },
    "toast_deleted": {
        "fr": "Livre supprimé avec succès !", "tr": "Kitap başarıyla silindi!", "en": "Book deleted successfully!",
        "bg": "Книгата е изтрита успешно!", "de": "Buch erfolgreich gelöscht!", "ar": "تم حذف الكتاب بنجاح!",
        "es": "¡Libro eliminado con éxito!", "it": "Libro eliminato con successo!", "ru": "Книга успешно удалена!"
    },
    "shared_by": {
        "fr": "Partagé par :", "tr": "Paylaşan:", "en": "Shared by:",
        "bg": "Споделено от:", "de": "Geteilt von:", "ar": "بواسطة:",
        "es": "Compartido por:", "it": "Condiviso da:", "ru": "От:"
    }
}

if "app_lang" not in st.session_state:
    st.session_state.app_lang = "bg"

def txt(key):
    lang = st.session_state.app_lang
    if key in I18N:
        return I18N[key].get(lang, I18N[key].get("en", key))
    return key

# ==========================================
# 1. VERİTABANI BAĞLANTISI (GOOGLE SHEETS)
# ==========================================
SPREADSHEET_ID = "1Ec0v2Oo-7BlILvb35TGgo5j-SOGivJwmf5xpF85oGoU"  # Kendi Google Sheet ID'niz

@st.cache_resource
def get_gspread_client():
    try:
        # Önce Streamlit Cloud Secrets (Bulut) kontrolü
        if "gcp_service_account" in st.secrets:
            return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
        # Bulut değilse yerel JSON dosyasını (google_secret.json) okur
        return gspread.service_account(filename="google_secret.json")
    except Exception as e:
        st.error(f"Kimlik doğrulama hatası: {e}")
        return None

gc = get_gspread_client()

@st.cache_resource
def get_spreadsheet():
    if gc:
        try:
            return gc.open_by_key(SPREADSHEET_ID)
        except Exception:
            return None
    return None

def get_sheet(sheet_name):
    sh = get_spreadsheet()
    if sh:
        try:
            return sh.worksheet(sheet_name)
        except Exception:
            return None
    return None

@st.cache_data(ttl=120, show_spinner=False)
def fetch_data(sheet_name):
    sheet = get_sheet(sheet_name)
    if sheet:
        try:
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except APIError:
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def delete_book_from_db(book_id):
    sheet = get_sheet("Library")
    if sheet:
        try:
            all_vals = sheet.get_all_values()
            if all_vals:
                header = all_vals[0]
                remaining = [row for row in all_vals[1:] if len(row) > 0 and str(row[0]).strip() != str(book_id).strip()]
                sheet.clear()
                sheet.update([header] + remaining)
                fetch_data.clear()
                return True
        except Exception as e:
            st.error(f"Silme hatası: {e}")
            return False
    return False

def compress_image_to_base64(img):
    img_copy = img.copy()
    img_copy.thumbnail((500, 500))
    if img_copy.mode != "RGB":
        img_copy = img_copy.convert("RGB")
    
    for quality in [50, 40, 30, 20]:
        buf = io.BytesIO()
        img_copy.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) < 45000:
            return b64_str
    return b64_str[:45000]

def base64_to_image(b64_str):
    img_data = base64.b64decode(b64_str)
    return Image.open(io.BytesIO(img_data))

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# Session State Değişkenleri
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_book" not in st.session_state:
    st.session_state.active_book = None
if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0
if "page_texts" not in st.session_state:
    st.session_state.page_texts = {}
if "upload_pages" not in st.session_state:
    st.session_state.upload_pages = [] 
if "show_editor" not in st.session_state:
    st.session_state.show_editor = False 

# --- OCR VE ÇEVİRİ FONKSİYONLARI ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['fr', 'en'], gpu=False)
reader = load_ocr()

@st.cache_data(show_spinner=False)
def direct_google_translate(text, target_lang, retries=3):
    if not text.strip(): return ""
    clients = ['gtx', 'dict-chrome-ex', 'te_lib']
    for attempt in range(retries):
        try:
            client = clients[attempt % len(clients)]
            url = f"https://translate.googleapis.com/translate_a/single?client={client}&sl=fr&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            response = urllib.request.urlopen(req, timeout=7)
            result = json.loads(response.read().decode('utf-8'))
            translated_text = ""
            for sentence in result[0]:
                if sentence[0]: translated_text += sentence[0]
            return translated_text
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1 + random.uniform(0, 1))
                continue
            else:
                return f"Çeviri hatası: {e}"
        except Exception as e:
            return f"Çeviri hatası: {e}"
    return "Çeviri servisi geçici olarak meşgul. Lütfen birkaç saniye sonra tekrar deneyin."

@st.cache_data(show_spinner=False)
def get_dictionary_direct(words_list, dest_lang):
    clean_words = list(set([re.sub(r"[^\wÀ-ÿ'-]", "", w).strip().lower() for w in words_list if re.sub(r"[^\wÀ-ÿ'-]", "", w).strip()]))
    if not clean_words: return {}
    separator = " | "
    combined_text = separator.join(clean_words)
    trans_map = {}
    try:
        translated_text = direct_google_translate(combined_text, dest_lang)
        if "Çeviri" in translated_text and "hatası" in translated_text:
            raise Exception("API Kota Limiti")
        translated_words = [w.strip() for w in translated_text.split(separator.strip())]
        for i, word in enumerate(clean_words):
            if i < len(translated_words): trans_map[word] = translated_words[i].replace('|', '').strip()
            else: trans_map[word] = "-"
    except Exception:
        for word in clean_words: trans_map[word] = "-"
    return trans_map

# ==========================================
# 2. YAN MENÜ (DİL SEÇİCİ & KULLANICI İŞLEMLERİ)
# ==========================================
with st.sidebar:
    st.markdown("### 🌐 Langue / Dil / Language")
    lang_keys = list(LANGUAGES.keys())
    current_idx = lang_keys.index(st.session_state.app_lang) if st.session_state.app_lang in lang_keys else 0
    selected_lang = st.selectbox(
        "Dil Seçimi",
        options=lang_keys,
        format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
        index=current_idx,
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.app_lang:
        st.session_state.app_lang = selected_lang
        st.rerun()

    st.divider()

    if st.session_state.current_user is None:
        st.header(txt("sidebar_account"))
        login_tab, signup_tab = st.tabs([txt("tab_login"), txt("tab_signup")])
        
        with login_tab:
            l_email = st.text_input(txt("email_label"), key="l_email").strip()
            l_pass = st.text_input(txt("password_label"), type="password", key="l_pass")
            if st.button(txt("tab_login"), use_container_width=True):
                users_df = fetch_data("Users")
                if not users_df.empty:
                    user_match = users_df[(users_df['Email'].astype(str) == l_email) & (users_df['Password'].astype(str) == l_pass)]
                    if not user_match.empty:
                        st.session_state.current_user = {
                            "email": l_email, 
                            "nickname": user_match.iloc[0]['Nickname'], 
                            "role": user_match.iloc[0]['Role']
                        }
                        st.success(f"{txt('welcome_msg')}, {user_match.iloc[0]['Nickname']}!")
                        st.rerun()
                    else:
                        st.error(txt("invalid_creds"))
                else:
                    st.error("Veritabanı okunamadı.")
        
        with signup_tab:
            s_email = st.text_input(txt("email_label"), key="s_email").strip()
            s_nick = st.text_input(txt("nickname_label"), key="s_nick").strip()
            s_pass = st.text_input(txt("password_label"), type="password", key="s_pass")
            if st.button(txt("tab_signup"), use_container_width=True):
                if s_email and s_nick and s_pass:
                    users_df = fetch_data("Users")
                    if not users_df.empty and s_email in users_df['Email'].astype(str).values:
                        st.error(txt("email_exists"))
                    else:
                        sheet = get_sheet("Users")
                        if sheet:
                            try:
                                sheet.append_row([s_email, s_nick, s_pass, "user", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                                fetch_data.clear()
                                st.success(txt("signup_success"))
                            except Exception as ex:
                                st.error(f"Erreur: {ex}")
                else:
                    st.warning(txt("fill_all_fields"))
        st.divider()
    else:
        st.header(f"👋 {st.session_state.current_user['nickname']}")
        if st.button(txt("btn_logout"), use_container_width=True):
            st.session_state.current_user = None
            st.session_state.active_book = None
            st.session_state.page_texts = {}
            st.session_state.page_idx = 0
            st.session_state.upload_pages = []
            st.session_state.show_editor = False
            st.rerun()
            
        st.divider()
        st.markdown(f"### {txt('sidebar_community')}")
        if st.button(txt("thank_tolga"), use_container_width=True):
            sheet = get_sheet("Thanks")
            if sheet:
                try:
                    sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.current_user['email'], st.session_state.current_user['nickname']])
                    fetch_data.clear()
                    st.toast(txt("toast_thank"), icon="🎉")
                    st.balloons()
                except Exception as ex:
                    st.error(f"Erreur: {ex}")

    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #64748b; padding-top: 10px;'>
            <small>Lycée Français Victor Hugo<br>
            Powered by <b>Tolga Küreç</b><br>
            <i>(Father of Timuçin and Teoman)</i></small>
        </div>
        """, unsafe_allow_html=True
    )

# ==========================================
# 3. ANA EKRAN - SEKMELER
# ==========================================
st.title(txt("title"))

tab_read, tab_my_lib, tab_community, tab_admin = st.tabs([
    txt("tab_read"), 
    txt("tab_my_lib"), 
    txt("tab_community"), 
    txt("tab_admin")
])

# ----- SEKME 1: OKUMA VE ÇEVİRİ ALANI -----
with tab_read:
    if st.session_state.active_book:
        st.info(f"{txt('open_book_info')} **{st.session_state.active_book['name']}**")
        if st.button(txt("close_book"), use_container_width=True):
            st.session_state.active_book = None
            st.session_state.page_idx = 0
            st.session_state.page_texts = {}
            st.session_state.upload_pages = []
            st.session_state.show_editor = False
            st.rerun()
        pages_to_display = st.session_state.active_book["pages"]
    else:
        if not st.session_state.show_editor:
            st.markdown(f"### {txt('step1_title')}")
            uploaded_raw = st.file_uploader(
                txt("step1_uploader"), 
                type=["png", "jpg", "jpeg"], 
                accept_multiple_files=True
            )
            if uploaded_raw:
                sorted_files = sorted(uploaded_raw, key=lambda f: natural_sort_key(f.name))
                st.session_state.upload_pages = []
                for idx, file in enumerate(sorted_files):
                    try:
                        raw_img = Image.open(file)
                        img = ImageOps.exif_transpose(raw_img)
                    except Exception:
                        img = Image.open(file)
                    st.session_state.upload_pages.append({
                        "id": f"upload_{file.name}_{idx}",
                        "image": img,
                        "name": file.name,
                        "text": None
                    })
                if st.button(txt("step1_btn"), type="primary"):
                    st.session_state.show_editor = True
                    st.rerun()
        
        else:
            st.markdown(f"### {txt('step2_title')}")
            st.caption(txt("step2_desc"))
            for i, page in enumerate(st.session_state.upload_pages):
                c_img, c_info, c_btn1, c_btn2, c_btn3 = st.columns([1, 4, 1, 1, 1])
                thumb = page["image"].copy()
                thumb.thumbnail((100, 100))
                c_img.image(thumb)
                
                c_info.markdown(f"**{txt('page_label')} {i+1}** <br> <small>{page['name']}</small>", unsafe_allow_html=True)
                
                if c_btn1.button("⬆️", key=f"up_{i}", disabled=(i == 0)):
                    st.session_state.upload_pages[i], st.session_state.upload_pages[i-1] = st.session_state.upload_pages[i-1], st.session_state.upload_pages[i]
                    st.rerun()
                    
                if c_btn2.button("⬇️", key=f"down_{i}", disabled=(i == len(st.session_state.upload_pages) - 1)):
                    st.session_state.upload_pages[i], st.session_state.upload_pages[i+1] = st.session_state.upload_pages[i+1], st.session_state.upload_pages[i]
                    st.rerun()
                    
                if c_btn3.button("🗑️", key=f"del_{i}"):
                    st.session_state.upload_pages.pop(i)
                    st.rerun()
            
            st.divider()
            col1, col2 = st.columns(2)
            if col1.button(txt("step2_back")):
                st.session_state.show_editor = False
                st.session_state.upload_pages = []
                st.rerun()
                
            if len(st.session_state.upload_pages) > 0:
                if col2.button(txt("step2_done"), type="primary"):
                    st.session_state.active_book = {
                        "name": "Nouveau livre", 
                        "pages": st.session_state.upload_pages,
                        "is_temp": True
                    }
                    st.session_state.page_idx = 0
                    st.session_state.show_editor = False
                    st.rerun()

    # --- OKUMA ALANI ---
    if st.session_state.active_book:
        pages_to_display = st.session_state.active_book["pages"]
        total_pages = len(pages_to_display)
        if st.session_state.page_idx >= total_pages:
            st.session_state.page_idx = max(0, total_pages - 1)

        nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])
        with nav_c1:
            if st.button(txt("prev_page"), disabled=(st.session_state.page_idx == 0), use_container_width=True):
                st.session_state.page_idx -= 1
                st.rerun()
        with nav_c2:
            st.markdown(f"<h4 style='text-align: center; margin: 0;'>{txt('page_label')} {st.session_state.page_idx + 1} / {total_pages}</h4>", unsafe_allow_html=True)
        with nav_c3:
            if st.button(txt("next_page"), disabled=(st.session_state.page_idx == total_pages - 1), use_container_width=True):
                st.session_state.page_idx += 1
                st.rerun()

        st.divider()

        current_page = pages_to_display[st.session_state.page_idx]
        image = current_page["image"]
        page_key = current_page["id"]

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.subheader(f"📖 {txt('page_label')}")
            rotation_angle = st.radio(txt("orientation"), options=[0, 90, 180, 270], format_func=lambda x: f"{x}°", horizontal=True, key=f"rot_{page_key}")
            if rotation_angle != 0:
                image = image.rotate(-rotation_angle, expand=True)
            st.image(image, use_container_width=True)

            if st.session_state.active_book.get("is_temp"):
                st.divider()
                st.markdown(f"### {txt('save_header')}")
                book_title = st.text_input(txt("book_name"), placeholder="Ex: Le Petit Poucet", key="save_book_name")
                is_shared_check = st.checkbox(txt("share_opt"), value=True)
                
                can_save = st.session_state.current_user is not None
                if st.button(txt("btn_save"), disabled=not can_save, use_container_width=True):
                    if not book_title.strip():
                        st.warning("Boş bırakılamaz / Cannot be empty.")
                    else:
                        progress_bar = st.progress(0, text="Sauvegarde en cours...")
                        lib_sheet = get_sheet("Library")
                        if lib_sheet:
                            book_id = str(uuid.uuid4())[:8]
                            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            rows_to_append = []
                            
                            for p_num, p_data in enumerate(pages_to_display):
                                p_img = p_data["image"]
                                p_k = p_data["id"]
                                
                                if p_k in st.session_state.page_texts:
                                    p_txt = st.session_state.page_texts[p_k]
                                else:
                                    ocr_r = reader.readtext(np.array(p_img.convert('L')), detail=0, paragraph=True, width_ths=0.8, mag_ratio=1.5)
                                    p_txt = " ".join(ocr_r).strip()
                                
                                img_b64 = compress_image_to_base64(p_img)
                                rows_to_append.append([
                                    book_id, created_at, st.session_state.current_user['email'],
                                    st.session_state.current_user['nickname'], book_title,
                                    "YES" if is_shared_check else "NO", p_num + 1, p_txt, img_b64
                                ])
                                progress_bar.progress((p_num + 1) / len(pages_to_display))
                            
                            try:
                                lib_sheet.append_rows(rows_to_append)
                                fetch_data.clear()
                                st.session_state.active_book["is_temp"] = False
                                st.session_state.active_book["name"] = book_title
                                st.success(f"'{book_title}' enregistré avec succès!")
                                st.balloons()
                                st.rerun()
                            except APIError:
                                st.error("Google quota limite atteint. Veuillez patienter 1 minute.")
                            except Exception as save_err:
                                st.error(f"Erreur: {save_err}")
                        else:
                            st.error("Impossible d'accéder à la base de données.")
                if not can_save:
                    st.caption(txt("login_to_save"))

        with col_right:
            st.subheader(txt("ocr_header"))
            
            if current_page.get("text") and page_key not in st.session_state.page_texts:
                st.session_state.page_texts[page_key] = current_page["text"]
                
            if page_key not in st.session_state.page_texts:
                with st.spinner("Analyse du texte (OCR)..."):
                    img_gray = image.convert('L')
                    ocr_results = reader.readtext(np.array(img_gray), detail=0, paragraph=True, width_ths=0.8, mag_ratio=1.5)
                    st.session_state.page_texts[page_key] = " ".join(ocr_results).strip()

            edited_text = st.text_area(
                txt("edit_prompt"),
                value=st.session_state.page_texts[page_key],
                height=140,
                key=f"text_edit_{page_key}"
            )
            st.session_state.page_texts[page_key] = edited_text

            target_lang = st.session_state.app_lang
            target_flag = LANGUAGES[target_lang]["flag"]

            if st.button(txt("btn_translate"), use_container_width=True):
                if edited_text.strip():
                    with st.spinner("Traduction..."):
                        translated = direct_google_translate(edited_text, target_lang)
                        st.success(f"**Traduction ({target_flag}):**\n\n{translated}")

            st.divider()

            if edited_text.strip():
                raw_words = re.findall(r"[\wÀ-ÿ'-]+", edited_text)
                with st.spinner("Dictionnaire..."):
                    translations = get_dictionary_direct(raw_words, target_lang)

                safe_text = json.dumps(edited_text, ensure_ascii=False)
                safe_dict = json.dumps(translations, ensure_ascii=False)

                HTML_TEMPLATE = """
                <div style="font-family: sans-serif; padding: 15px; border-radius: 12px; background: #f8f9fa; border: 1px solid #e2e8f0;">
                    <div style="margin-bottom: 12px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                        <button onclick="playText()" style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer;">__BTN_PLAY__</button>
                        <button onclick="stopAudio()" style="background: #ef4444; color: white; border: none; padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer;">__BTN_STOP__</button>
                    </div>
                    <div id="storyContainer" style="font-size: 20px; line-height: 2; padding: 16px; background: white; border-radius: 10px; max-height: 250px; overflow-y: auto; border: 1px solid #cbd5e1;"></div>
                    <div id="tooltipCard" style="margin-top: 14px; padding: 12px; background: #e0f2fe; border-left: 4px solid #0284c7; border-radius: 6px; display: none;">
                        <span id="wordDetail" style="font-size: 16px; font-weight: 600; color: #0369a1;"></span>
                    </div>
                </div>
                <style>
                    .karaoke-word { cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: 0.1s; display: inline-block; color: #1e293b; }
                    .karaoke-word:hover { background: #e2e8f0; }
                    .karaoke-active { background-color: #fde047 !important; color: #000 !important; font-weight: bold; transform: scale(1.05); box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
                </style>
                <script>
                    const rawText = __RAW_TEXT__;
                    const dictionary = __DICT_DATA__;
                    const targetFlag = "__TARGET_FLAG__";
                    let synth = window.speechSynthesis;
                    let wordMap = []; 
                    let timerId = null;
                    let isPlaying = false;
                    
                    function renderText() {
                        const container = document.getElementById("storyContainer");
                        container.innerHTML = "";
                        wordMap = [];
                        const regex = /([\\wÀ-ÿ'-]+)/g;
                        let match; let lastIdx = 0;
                        while ((match = regex.exec(rawText)) !== null) {
                            let word = match[0]; let start = match.index; let end = start + word.length;
                            if (start > lastIdx) container.appendChild(document.createTextNode(rawText.substring(lastIdx, start)));
                            const span = document.createElement("span");
                            span.className = "karaoke-word"; span.innerText = word; span.id = "w_" + wordMap.length;
                            span.dataset.clean = word.toLowerCase();
                            span.onclick = () => selectWord(span.innerText, span.dataset.clean);
                            container.appendChild(span);
                            wordMap.push({ id: span.id, text: word, length: word.length });
                            lastIdx = end;
                        }
                        if (lastIdx < rawText.length) container.appendChild(document.createTextNode(rawText.substring(lastIdx)));
                    }
                    function simulateHighlighting() {
                        let idx = 0;
                        function nextWord() {
                            if(!isPlaying || idx >= wordMap.length) return;
                            document.querySelectorAll(".karaoke-word").forEach(el => el.classList.remove("karaoke-active"));
                            const el = document.getElementById(wordMap[idx].id);
                            if(el) { el.classList.add("karaoke-active"); el.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" }); }
                            let duration = ((wordMap[idx].length * 65) + 30) / 0.85;
                            if (rawText.substring(rawText.indexOf(wordMap[idx].text) + wordMap[idx].length, rawText.indexOf(wordMap[idx].text) + wordMap[idx].length + 1).match(/[.,;:?!]/)) duration += 300 / 0.85;
                            idx++; timerId = setTimeout(nextWord, duration);
                        }
                        timerId = setTimeout(nextWord, 300 / 0.85); 
                    }
                    function playText() {
                        stopAudio(); isPlaying = true;
                        const utterance = new SpeechSynthesisUtterance(rawText);
                        utterance.lang = 'fr-FR'; utterance.rate = 0.85;
                        const voices = synth.getVoices();
                        let frVoice = voices.find(v => v.lang === 'fr-FR' && v.name.includes('Google'));
                        if (!frVoice) frVoice = voices.find(v => v.lang.startsWith('fr'));
                        if (frVoice) utterance.voice = frVoice;
                        utterance.onend = stopAudio; utterance.onerror = stopAudio;
                        synth.speak(utterance); simulateHighlighting();
                    }
                    function stopAudio() { isPlaying = false; synth.cancel(); clearTimeout(timerId); document.querySelectorAll(".karaoke-word").forEach(el => el.classList.remove("karaoke-active")); }
                    function selectWord(original, clean) {
                        const tr = dictionary[clean] || "-";
                        const card = document.getElementById("tooltipCard");
                        document.getElementById("wordDetail").innerText = "🇫🇷 " + original + " ➔ " + targetFlag + " " + tr;
                        card.style.display = "block";
                        synth.cancel();
                        let u = new SpeechSynthesisUtterance(original); u.lang = 'fr-FR'; u.rate = 0.8; synth.speak(u);
                    }
                    window.onload = renderText; setTimeout(renderText, 100);
                </script>
                """
                rendered_html = (
                    HTML_TEMPLATE
                    .replace("__RAW_TEXT__", safe_text)
                    .replace("__DICT_DATA__", safe_dict)
                    .replace("__TARGET_FLAG__", target_flag)
                    .replace("__BTN_PLAY__", txt("btn_play"))
                    .replace("__BTN_STOP__", txt("btn_stop"))
                )
                components.html(rendered_html, height=450, scrolling=False)

# ----- SEKME 2: KÜTÜPHANEM -----
with tab_my_lib:
    if st.session_state.current_user is None:
        st.warning(txt("login_for_lib"))
    else:
        st.markdown(f"### 📚 {st.session_state.current_user['nickname']}")
        lib_df = fetch_data("Library")
        
        if not lib_df.empty and "OwnerEmail" in lib_df.columns:
            my_books = lib_df[lib_df['OwnerEmail'].astype(str) == st.session_state.current_user['email']]
            if not my_books.empty:
                grouped = my_books.groupby("BookID")
                for book_id, group in grouped:
                    b_title = group.iloc[0]['BookName']
                    b_date = group.iloc[0]['CreatedAt']
                    b_shared = group.iloc[0]['IsShared']
                    p_count = len(group)
                    
                    with st.expander(f"📖 {b_title} ({p_count} {txt('page_label')}) - {b_date}"):
                        c1, c2, c3 = st.columns([2.5, 1, 1])
                        c1.write(f"**Statut:** {txt('status_shared') if b_shared == 'YES' else txt('status_private')}")
                        
                        if c2.button(txt("btn_read"), key=f"open_my_{book_id}", use_container_width=True):
                            loaded_pages = []
                            sorted_group = group.sort_values("PageNum")
                            for _, row in sorted_group.iterrows():
                                loaded_pages.append({
                                    "id": f"saved_{book_id}_{row['PageNum']}",
                                    "image": base64_to_image(row['ImageBase64']),
                                    "text": row['OCRText']
                                })
                            st.session_state.active_book = {"name": b_title, "pages": loaded_pages, "is_temp": False}
                            st.session_state.page_idx = 0
                            st.session_state.page_texts = {}
                            st.rerun()
                            
                        if c3.button(txt("btn_delete"), key=f"del_my_{book_id}", use_container_width=True):
                            if delete_book_from_db(book_id):
                                if st.session_state.active_book and st.session_state.active_book.get("name") == b_title:
                                    st.session_state.active_book = None
                                st.toast(txt("toast_deleted"), icon="🗑️")
                                st.rerun()
            else:
                st.info(txt("no_books_my"))
        else:
            st.info(txt("lib_empty"))

# ----- SEKME 3: ORTAK KÜTÜPHANE -----
with tab_community:
    st.markdown(f"### {txt('tab_community')}")
    st.caption(txt("community_desc"))
    
    lib_df = fetch_data("Library")
    if not lib_df.empty and "IsShared" in lib_df.columns:
        shared_books = lib_df[lib_df['IsShared'].astype(str) == "YES"]
        if not shared_books.empty:
            grouped = shared_books.groupby("BookID")
            for book_id, group in grouped:
                b_title = group.iloc[0]['BookName']
                b_owner_nick = group.iloc[0]['OwnerNickname']
                p_count = len(group)
                
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"#### 📖 {b_title}")
                        st.caption(f"👤 {txt('shared_by')} **{b_owner_nick}** | 📄 {p_count} {txt('page_label')}")
                    with col_btn:
                        if st.button(txt("btn_read"), key=f"open_comm_{book_id}", use_container_width=True):
                            loaded_pages = []
                            sorted_group = group.sort_values("PageNum")
                            for _, row in sorted_group.iterrows():
                                loaded_pages.append({
                                    "id": f"saved_{book_id}_{row['PageNum']}",
                                    "image": base64_to_image(row['ImageBase64']),
                                    "text": row['OCRText']
                                })
                            st.session_state.active_book = {"name": b_title, "pages": loaded_pages, "is_temp": False}
                            st.session_state.page_idx = 0
                            st.session_state.page_texts = {}
                            st.rerun()
        else:
            st.info(txt("no_books_comm"))
    else:
        st.info(txt("lib_empty"))

# ----- SEKME 4: YÖNETİCİ PANELİ (SADECE TOLGA) -----
with tab_admin:
    if st.session_state.current_user and st.session_state.current_user['role'] == "admin":
        st.markdown(f"### {txt('tab_admin')} (Tolga Küreç)")
        
        users_df = fetch_data("Users")
        st.markdown(f"#### {txt('admin_users')}")
        if not users_df.empty:
            cols = ["Nickname", "Email", "Role"]
            valid_cols = [c for c in cols if c in users_df.columns]
            st.dataframe(users_df[valid_cols], use_container_width=True)
        else:
            st.info(txt("admin_no_users"))
            
        st.divider()
        st.markdown(f"#### {txt('admin_thanks')}")
        thanks_df = fetch_data("Thanks")
        if not thanks_df.empty:
            st.dataframe(thanks_df.iloc[::-1], use_container_width=True)
        else:
            st.info(txt("admin_no_thanks"))
    else:
        st.error(txt("admin_only"))