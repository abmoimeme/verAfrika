"use strict";
/* VeraAfrika pilot UI. Every value comes from the API; the server decides what each user may see. */

const I18N = {
  fr: {
    skip: "Aller au contenu", nav: "Navigation principale",
    footer_staging: "Besoin d'aide ? Contactez votre référent pilote VeraAfrika.",
    err_401_pw: "Votre session a expiré. Connectez-vous à nouveau.", err_credentials: "E-mail ou mot de passe incorrect.",
    err_code: "Ce code ne fonctionne pas. Saisissez le code à 6 chiffres affiché actuellement par votre application.",
    err_too_many: "Trop de tentatives. Patientez 15 minutes puis réessayez.", err_invite: "Ce lien d'invitation n'est plus valide. Demandez-en un nouveau à votre référent VeraAfrika.",
    err_account_exists: "Un compte existe déjà pour cette adresse. Connectez-vous ou demandez de l'aide.",
    pw_min_length: "Utilisez au moins 12 caractères.", pw_max_length: "Utilisez 128 caractères au maximum.", pw_predictable: "Choisissez un mot de passe moins prévisible.",
    err_name: "Saisissez votre nom.", err_fields: "Saisissez votre e-mail et votre mot de passe.",
    auth_title: "Se connecter", email: "Adresse e-mail", password: "Mot de passe", show_pw: "Afficher le mot de passe", sign_in: "Se connecter",
    sign_out: "Se déconnecter", signin_help: "Accès sur invitation pendant le pilote. Mot de passe oublié ? Contactez votre référent pilote VeraAfrika.",
    env_staging: "Environnement pilote. L'appel d'offres affiché est une donnée de test synthétique ; les comptes sont réels.",
    mfa_title: "Vérification en deux étapes", mfa_setup_intro: "Votre compte d'équipe VeraAfrika doit être protégé par une application d'authentification (Google Authenticator, Microsoft Authenticator, 1Password…).",
    mfa_step1: "Ajoutez VeraAfrika dans votre application avec cette clé de configuration :", mfa_open_app: "Ouvrir dans l'application d'authentification",
    mfa_step2: "Saisissez le code à 6 chiffres affiché par l'application.", mfa_code: "Code à 6 chiffres", mfa_verify_intro: "Saisissez le code actuel de votre application d'authentification.",
    verify: "Vérifier", invite_title: "Créer votre compte", invite_for: (o, e) => `Invitation pour ${e} — ${o}.`,
    your_name: "Votre nom", pw_rule: "Au moins 12 caractères. Une phrase de passe facile à retenir convient très bien.",
    language: "Langue préférée", create_account: "Créer mon compte",
    reset_title: "Choisir un nouveau mot de passe", reset_for: (e) => `Compte : ${e}.`, save_password: "Enregistrer le mot de passe",
    env: "Environnement pilote : entreprises d'exemple et avis synthétique. Connexion de développement (sera remplacée par la connexion gérée).",
    footer: "Besoin d'aide ? Contactez votre référent pilote VeraAfrika. Les données affichées dans cet environnement sont des exemples.",
    signin_title: "Choisir un profil de test", signin_intro: "Connexion de développement. Chaque profil a une organisation, un rôle et un abonnement différents.",
    switch: "Changer de profil", signed_as: "Connecté·e :",
    nav_opps: "Appels d'offres", nav_bids: "Mes soumissions", nav_alerts: "Alertes", nav_review: "File de revue",
    nav_sources: "Sources et collectes", nav_trace: "Traçabilité", nav_audit: "Journal d'audit",
    opps_title: "Appels d'offres", search: "Rechercher", search_label: "Mots-clés", search_hint: "Titre, autorité contractante ou référence",
    country: "Pays", sector: "Secteur", all_sectors: "Tous les secteurs", apply: "Rechercher",
    results: n => n === 1 ? "1 appel d'offres" : `${n} appels d'offres`,
    empty: "Aucun appel d'offres ne correspond. Essayez d'autres mots-clés ou retirez le filtre secteur.",
    coverage_off: (c, s) => `VeraAfrika ne collecte pas encore les appels d'offres pour ce pays (${c}). Statut de couverture : ${s}. Une liste vide ne signifie pas qu'il n'existe aucun appel d'offres.`,
    coverage_on: d => `Source active. Dernière collecte réussie : ${d}.`,
    deadline: "Date limite de dépôt", issuer: "Autorité contractante", source: "Source", observed: "Observé le",
    sample: "Données d'exemple", amended: "Modifié par additif", pending_confirm: "Modification de l'émetteur — confirmation en cours", reviewed: "Vérifié par un analyste",
    days_left: n => n === 0 ? "Clôture aujourd'hui" : n === 1 ? "Il reste 1 jour" : `Il reste ${n} jours`, closed: "Clôturé",
    back: "Retour aux appels d'offres", summary: "Résumé", reference: "Référence", procedure: "Procédure", place: "Lieu d'exécution",
    value: "Montant estimé", lots: "Lots", lot: "Lot", bid_security: "Garantie de soumission", requirements: "Critères de qualification",
    eligible_countries: "Pays éligibles", industry: "Secteur d'activité",
    amend_note: (ref, d) => `${ref || "Un additif"} publié par l'émetteur, détecté le ${d}.`, previously: "Auparavant :",
    history: "Historique des modifications", hist_change: (f) => `Champ modifié : ${f}`,
    newer_review: "Une nouvelle version de la source est en cours de revue par nos analystes.",
    match: "Adéquation avec votre entreprise", eligible: "Éligible", not_eligible: "Non éligible", score: "Score", confidence: "Confiance",
    conf: { high: "élevée", medium: "moyenne", low: "faible" }, strengths: "Points forts", gaps: "Écarts", limitations: "Limites",
    rule_version: v => `Règles d'adéquation ${v}`,
    open_source: "Ouvrir la source d'origine", attribution: "Attribution", checksum: "Empreinte de l'enregistrement",
    gate_details: "Les détails complets, les lots, l'historique et l'adéquation sont inclus à partir de l'offre Compete.",
    gate_source: "Le lien vers la source d'origine est inclus à partir de l'offre Compete.",
    gate_bid: "Les espaces de soumission sont inclus à partir de l'offre Compete.", gate_role: "Votre rôle ne permet pas de démarrer une soumission. Demandez au responsable de votre organisation.",
    save: "Enregistrer", saved: "Enregistré", saved_msg: "Appel d'offres enregistré. Vous serez alerté·e en cas de modification.", unsaved_msg: "Appel d'offres retiré de vos favoris.",
    start_bid: "Démarrer une soumission", open_bid: "Ouvrir l'espace de soumission",
    confirm_title: "Démarrer une soumission ?", confirm_body: (d) => `Un espace de soumission sera créé pour votre organisation. Date limite actuelle : ${d}.`,
    confirm_limit: "Votre offre Compete inclut 1 espace de soumission actif à la fois.", cancel: "Annuler", confirm: "Démarrer",
    retry: "Réessayer", bid_started: "Espace de soumission créé",
    bid_next: "Prochaines étapes : relisez les critères de qualification et préparez vos pièces. La liste de contrôle des documents et les tâches d'équipe arrivent dans une prochaine version.",
    bids_title: "Mes soumissions", bids_empty: "Aucune soumission en cours. Démarrez-en une depuis un appel d'offres.",
    started_on: "Démarrée le", status: "Statut", st_active: "En cours", version_at_start: v => `Version de l'avis au démarrage : ${v}`,
    alerts_title: "Alertes", alerts_empty: "Aucune alerte pour le moment.", mark_read: "Marquer comme lue", read: "Lue", unread: "Non lue",
    al_deadline: "La date limite a changé", al_pursuit: "Soumission démarrée", al_amend: "Avis modifié",
    loading: "Chargement…",
    review_title: "File de revue", rv_priority: "Priorité", rv_kind: "Type", rv_notice: "Avis", rv_version: "Version", rv_due: "Échéance",
    pr_high: "Haute", pr_normal: "Normale", k_new: "Nouvel avis", k_amend: "Additif", overdue: "En retard", review_empty: "Aucune tâche ouverte.",
    open: "Ouvrir",
    task_title: "Revue de l'avis", extracted: "Champs extraits", raw: "Enregistrement source brut (non modifiable)", origin: "Origine",
    o_source: "Source", o_analyst: "Analyste", correct: "Corriger", new_value: "Nouvelle valeur", reason: "Motif de la correction",
    reason_hint: "Obligatoire. Il sera visible dans la traçabilité.", save_corr: "Enregistrer la correction", corr_saved: "Correction enregistrée. L'enregistrement brut est inchangé.",
    approve: "Approuver et publier", approve_note: "Note (facultatif)", reject: "Rejeter", reject_note: "Motif du rejet",
    approved_msg: "Version approuvée et publiée.", rejected_msg: "Version rejetée.", reject_blocked: "Cet additif est déjà visible par les clients ; corrigez puis approuvez.",
    amendment: "Additif détecté", field: "Champ", old: "Ancienne valeur", new: "Nouvelle valeur", retrieved: "Collecté le",
    sources_title: "Sources et collectes", rights: "Droits", run_initial: "Collecter : instantané initial", run_amend: "Collecter : additif n°1", run_candidate: "Lancer une collecte",
    runs: "Collectes récentes", run_ok: r => `Collecte terminée : ${r.records_new} nouveau(x), ${r.records_amended} modifié(s), ${r.records_unchanged} inchangé(s).`,
    r_started: "Début", r_status: "Statut", r_counts: "Nouveaux / modifiés / inchangés", r_error: "Erreur",
    rights_approved: "Approuvée", rights_pending: "Revue des droits en cours", rights_denied: "Refusée",
    trace_title: "Traçabilité", trace_pick: "Choisissez un avis", trace_field: "Champ à retracer", all_fields: "Tous les champs",
    version: v => `Version ${v}`, run: "Collecte", record: "Enregistrement source", by: "par", superseded: "remplacée",
    audit_title: "Journal d'audit", a_when: "Date", a_action: "Action", a_actor: "Acteur", a_object: "Objet",
    err_401: "Votre session a expiré. Choisissez à nouveau un profil.", err_404: "Cette page est introuvable ou n'est pas accessible avec votre compte.",
    err_403_plan: p => `Cette action nécessite l'offre ${p}.`, err_403: "Votre accès ne permet pas cette action.",
    err_409_idem: "Cette demande a changé pendant son envoi. Vérifiez puis réessayez.", err_422: "Une revue par un analyste est nécessaire avant cette action.",
    err_429: (l, p) => `Limite de votre offre atteinte (${l}). Passez à l'offre ${p} pour en avoir davantage.`,
    err_503: "La source est momentanément indisponible. Les dernières données connues sont affichées.",
    err_network: "Connexion impossible. Vérifiez votre réseau puis réessayez. Rien n'a été perdu.",
    err_generic: "Une erreur est survenue. Réessayez dans un instant.", err_pursuit_exists: "Votre organisation a déjà un espace de soumission pour cet appel d'offres.",
    err_closed: "La date limite de cet appel d'offres est passée.",
    decision: "Décision", value_col: "Valeur", details_col: "Détails", published: "Publiée", system: "système",
    roles: { owner: "Responsable", viewer: "Lecture seule", analyst: "Analyste", auditor: "Auditeur" },
    run_st: { succeeded: "Réussie", failed: "Échouée", running: "En cours" },
    rev_st: { pending_review: "En attente de revue", published_pending_confirmation: "Publiée, confirmation en cours", approved: "Approuvée", rejected: "Rejetée" },
    plans: { discover: "Discover", compete: "Compete", grow: "Grow", enterprise: "Enterprise" },
    states: { not_researched: "non étudiée", discovery: "en exploration", rights_review: "revue des droits", active: "active", degraded: "dégradée" },
  },
  en: {
    skip: "Skip to content", nav: "Main navigation",
    footer_staging: "Need help? Contact your VeraAfrika pilot lead.",
    err_401_pw: "Your session has expired. Sign in again.", err_credentials: "Email or password is incorrect.",
    err_code: "That code didn't work. Enter the 6-digit code your app shows right now.",
    err_too_many: "Too many attempts. Wait 15 minutes, then try again.", err_invite: "This invitation link is no longer valid. Ask your VeraAfrika contact for a new one.",
    err_account_exists: "An account already exists for this email. Sign in instead, or ask for help.",
    pw_min_length: "Use at least 12 characters.", pw_max_length: "Use 128 characters or fewer.", pw_predictable: "Choose a less predictable password.",
    err_name: "Enter your name.", err_fields: "Enter your email and password.",
    auth_title: "Sign in", email: "Email address", password: "Password", show_pw: "Show password", sign_in: "Sign in",
    sign_out: "Sign out", signin_help: "Access is by invitation during the pilot. Forgot your password? Contact your VeraAfrika pilot lead.",
    env_staging: "Pilot environment. The tender shown is synthetic test data; accounts are real.",
    mfa_title: "Two-step verification", mfa_setup_intro: "VeraAfrika team accounts must be protected with an authenticator app (Google Authenticator, Microsoft Authenticator, 1Password…).",
    mfa_step1: "Add VeraAfrika to your app with this setup key:", mfa_open_app: "Open in authenticator app",
    mfa_step2: "Enter the 6-digit code your app shows.", mfa_code: "6-digit code", mfa_verify_intro: "Enter the current code from your authenticator app.",
    verify: "Verify", invite_title: "Create your account", invite_for: (o, e) => `Invitation for ${e} — ${o}.`,
    your_name: "Your name", pw_rule: "At least 12 characters. An easy-to-remember passphrase works well.",
    language: "Preferred language", create_account: "Create my account",
    reset_title: "Choose a new password", reset_for: (e) => `Account: ${e}.`, save_password: "Save password",
    env: "Pilot environment: sample companies and a synthetic notice. Development sign-in (to be replaced by managed sign-in).",
    footer: "Need help? Contact your VeraAfrika pilot lead. Data shown in this environment is sample data.",
    signin_title: "Choose a test profile", signin_intro: "Development sign-in. Each profile has a different organization, role and plan.",
    switch: "Switch profile", signed_as: "Signed in:",
    nav_opps: "Tenders", nav_bids: "My bids", nav_alerts: "Alerts", nav_review: "Review queue",
    nav_sources: "Sources & runs", nav_trace: "Trace", nav_audit: "Audit log",
    opps_title: "Tenders", search: "Search", search_label: "Keywords", search_hint: "Title, issuing authority or reference",
    country: "Country", sector: "Sector", all_sectors: "All sectors", apply: "Search",
    results: n => n === 1 ? "1 tender" : `${n} tenders`,
    empty: "No tenders match. Try other keywords or remove the sector filter.",
    coverage_off: (c, s) => `VeraAfrika does not collect tenders for this country yet (${c}). Coverage status: ${s}. An empty list does not mean there are no tenders.`,
    coverage_on: d => `Source active. Last successful collection: ${d}.`,
    deadline: "Submission deadline", issuer: "Issuing authority", source: "Source", observed: "Observed",
    sample: "Sample data", amended: "Amended by issuer", pending_confirm: "Issuer amendment — confirmation in progress", reviewed: "Analyst reviewed",
    days_left: n => n === 0 ? "Closes today" : n === 1 ? "1 day left" : `${n} days left`, closed: "Closed",
    back: "Back to tenders", summary: "Summary", reference: "Reference", procedure: "Procedure", place: "Place of performance",
    value: "Estimated value", lots: "Lots", lot: "Lot", bid_security: "Bid security", requirements: "Qualification requirements",
    eligible_countries: "Eligible countries", industry: "Industry",
    amend_note: (ref, d) => `${ref || "An amendment"} published by the issuer, detected ${d}.`, previously: "Previously:",
    history: "Amendment history", hist_change: (f) => `Field changed: ${f}`,
    newer_review: "A newer version from the source is being reviewed by our analysts.",
    match: "Fit with your company", eligible: "Eligible", not_eligible: "Not eligible", score: "Score", confidence: "Confidence",
    conf: { high: "high", medium: "medium", low: "low" }, strengths: "Strengths", gaps: "Gaps", limitations: "Limitations",
    rule_version: v => `Matching rules ${v}`,
    open_source: "Open the original source", attribution: "Attribution", checksum: "Record fingerprint",
    gate_details: "Full details, lots, amendment history and company fit are included from the Compete plan.",
    gate_source: "The link to the original source is included from the Compete plan.",
    gate_bid: "Bid workspaces are included from the Compete plan.", gate_role: "Your role cannot start bids. Ask your organization owner.",
    save: "Save", saved: "Saved", saved_msg: "Tender saved. You'll be alerted if it changes.", unsaved_msg: "Tender removed from saved.",
    start_bid: "Start a bid", open_bid: "Open bid workspace",
    confirm_title: "Start a bid?", confirm_body: (d) => `A bid workspace will be created for your organization. Current deadline: ${d}.`,
    confirm_limit: "Your Compete plan includes 1 active bid workspace at a time.", cancel: "Cancel", confirm: "Start bid",
    retry: "Try again", bid_started: "Bid workspace started",
    bid_next: "Next: review the qualification requirements and gather your documents. A document checklist and team tasks are coming in a later release.",
    bids_title: "My bids", bids_empty: "No bids in progress. Start one from a tender.",
    started_on: "Started", status: "Status", st_active: "In progress", version_at_start: v => `Notice version when started: ${v}`,
    alerts_title: "Alerts", alerts_empty: "No alerts yet.", mark_read: "Mark as read", read: "Read", unread: "Unread",
    al_deadline: "Deadline changed", al_pursuit: "Bid started", al_amend: "Notice amended",
    loading: "Loading…",
    review_title: "Review queue", rv_priority: "Priority", rv_kind: "Type", rv_notice: "Notice", rv_version: "Version", rv_due: "Due",
    pr_high: "High", pr_normal: "Normal", k_new: "New notice", k_amend: "Amendment", overdue: "Overdue", review_empty: "No open tasks.",
    open: "Open",
    task_title: "Notice review", extracted: "Extracted fields", raw: "Raw source record (read-only)", origin: "Origin",
    o_source: "Source", o_analyst: "Analyst", correct: "Correct", new_value: "New value", reason: "Reason for correction",
    reason_hint: "Required. It is shown in the trace.", save_corr: "Save correction", corr_saved: "Correction saved. The raw record is unchanged.",
    approve: "Approve and publish", approve_note: "Note (optional)", reject: "Reject", reject_note: "Reason for rejection",
    approved_msg: "Version approved and published.", rejected_msg: "Version rejected.", reject_blocked: "This amendment is already visible to customers; correct it and approve instead.",
    amendment: "Amendment detected", field: "Field", old: "Old value", new: "New value", retrieved: "Retrieved",
    sources_title: "Sources & runs", rights: "Rights", run_initial: "Collect: initial snapshot", run_amend: "Collect: amendment no. 1", run_candidate: "Run collection",
    runs: "Recent runs", run_ok: r => `Run finished: ${r.records_new} new, ${r.records_amended} amended, ${r.records_unchanged} unchanged.`,
    r_started: "Started", r_status: "Status", r_counts: "New / amended / unchanged", r_error: "Error",
    rights_approved: "Approved", rights_pending: "Rights review pending", rights_denied: "Denied",
    trace_title: "Trace", trace_pick: "Choose a notice", trace_field: "Field to trace", all_fields: "All fields",
    version: v => `Version ${v}`, run: "Run", record: "Source record", by: "by", superseded: "superseded",
    audit_title: "Audit log", a_when: "When", a_action: "Action", a_actor: "Actor", a_object: "Object",
    err_401: "Your session has expired. Choose a profile again.", err_404: "This page can't be found or isn't available to your account.",
    err_403_plan: p => `This action requires the ${p} plan.`, err_403: "Your access doesn't include this action.",
    err_409_idem: "This request changed while it was being sent. Review and try again.", err_422: "Analyst review is needed before this action.",
    err_429: (l, p) => `You've reached your plan limit (${l}). Upgrade to ${p} for more.`,
    err_503: "The source is temporarily unavailable. The last known data is shown.",
    err_network: "Can't connect. Check your network and try again. Nothing was lost.",
    err_generic: "Something went wrong. Try again in a moment.", err_pursuit_exists: "Your organization already has a bid workspace for this tender.",
    err_closed: "The deadline for this tender has passed.",
    decision: "Decision", value_col: "Value", details_col: "Details", published: "Published", system: "system",
    roles: { owner: "Owner", viewer: "Read-only", analyst: "Analyst", auditor: "Auditor" },
    run_st: { succeeded: "Succeeded", failed: "Failed", running: "Running" },
    rev_st: { pending_review: "Pending review", published_pending_confirmation: "Published, confirmation pending", approved: "Approved", rejected: "Rejected" },
    plans: { discover: "Discover", compete: "Compete", grow: "Grow", enterprise: "Enterprise" },
    states: { not_researched: "not researched", discovery: "discovery", rights_review: "rights review", active: "active", degraded: "degraded" },
  },
};

const FIELD_LABELS = {
  fr: { title: "Titre", reference: "Référence", issuer: "Autorité contractante", procedure: "Procédure", published_on: "Date de publication",
        deadline: "Date limite", place: "Lieu d'exécution", lots: "Lots", qualification_requirements: "Critères de qualification",
        eligible_countries: "Pays éligibles", industry_code: "Code secteur VA", capability_tags: "Capacités requises",
        estimated_value: "Montant estimé", language: "Langue", issuer_amendment: "Additif" },
  en: { title: "Title", reference: "Reference", issuer: "Issuing authority", procedure: "Procedure", published_on: "Publication date",
        deadline: "Deadline", place: "Place of performance", lots: "Lots", qualification_requirements: "Qualification requirements",
        eligible_countries: "Eligible countries", industry_code: "VA industry code", capability_tags: "Required capabilities",
        estimated_value: "Estimated value", language: "Language", issuer_amendment: "Amendment" },
};
const CAPS = {
  fr: { solar_pumping: "pompage solaire", borehole_works: "travaux de forage", water_supply: "adduction d'eau" },
  en: { solar_pumping: "solar pumping", borehole_works: "borehole works", water_supply: "water supply" },
};
const MATCH_TEXT = {
  fr: {
    deadline_passed: () => "La date limite de dépôt est passée.",
    country_eligible: (p) => `Entreprise immatriculée dans un pays éligible (${p.country}).`,
    country_not_eligible: (p) => `Le pays de l'entreprise (${p.country}) n'est pas listé comme éligible.`,
    registration_active: (p) => `Immatriculation ${p.authority} active.`,
    registration_stale: (p) => `Statut d'immatriculation observé il y a plus de ${p.days} jours.`,
    registration_missing: () => "Aucune immatriculation active enregistrée. L'avis exige un RCCM valide.",
    industry_exact: () => "Le secteur de l'entreprise correspond à celui de l'avis.",
    industry_related: () => "L'entreprise travaille dans un secteur voisin du même pôle de marché.",
    industry_not_identical: () => "Secteur voisin, mais pas identique.",
    industry_mismatch: () => "Le secteur de l'entreprise ne correspond pas à l'avis.",
    capabilities_covered: (p) => `Capacités déclarées couvrant : ${capList(p.capabilities)}.`,
    capabilities_missing: (p) => `Aucune capacité déclarée pour : ${capList(p.capabilities)}.`,
    capabilities_self_declared: () => "Les capacités sont déclarées par l'entreprise et pas encore vérifiées.",
    sample_company: () => "Entreprise d'exemple utilisée pour le pilote.",
    decision_support_only: () => "Aide à la décision uniquement. Ce n'est pas une garantie d'éligibilité ni d'attribution.",
    experience_not_verified: () => "L'expérience exigée par l'avis n'a pas été vérifiée par VeraAfrika.",
  },
  en: {
    deadline_passed: () => "The submission deadline has passed.",
    country_eligible: (p) => `Registered in an eligible country (${p.country}).`,
    country_not_eligible: (p) => `Company country (${p.country}) is not listed as eligible.`,
    registration_active: (p) => `Registration ${p.authority} is active.`,
    registration_stale: (p) => `Registration status was last observed more than ${p.days} days ago.`,
    registration_missing: () => "No active registration on file. The notice requires a valid RCCM.",
    industry_exact: () => "Company industry matches the notice industry.",
    industry_related: () => "Company works in a related industry in the same market cluster.",
    industry_not_identical: () => "Industry is related, not identical.",
    industry_mismatch: () => "Company industry does not match the notice.",
    capabilities_covered: (p) => `Declared capabilities cover: ${capList(p.capabilities)}.`,
    capabilities_missing: (p) => `No declared capability for: ${capList(p.capabilities)}.`,
    capabilities_self_declared: () => "Capabilities are self-declared and not yet verified.",
    sample_company: () => "Sample company used for pilot testing.",
    decision_support_only: () => "Decision support only. It is not a guarantee of eligibility or of winning the tender.",
    experience_not_verified: () => "Past-contract experience required by the notice has not been verified by VeraAfrika.",
  },
};
const capList = (c) => (c || []).map((x) => CAPS[state.lang][x] || x).join(", ");
const matchText = (m) => (typeof m === "string" ? m : (MATCH_TEXT[state.lang][m.code] || (() => m.code))(m.params || {}));
const EDITABLE = ["title", "reference", "issuer", "procedure", "deadline", "place", "industry_code", "language"];
const COUNTRIES = [["SN", "Sénégal", "Senegal"], ["CI", "Côte d'Ivoire", "Côte d'Ivoire"], ["RW", "Rwanda", "Rwanda"], ["ML", "Mali", "Mali"], ["BF", "Burkina Faso", "Burkina Faso"]];

const state = { lang: "fr", me: null, unread: 0, flash: null, mode: "dev", mfa: null };
const $ = (s) => document.querySelector(s);
const t = (k, ...a) => { const v = I18N[state.lang][k]; return typeof v === "function" ? v(...a) : v ?? k; };
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fl = (f) => FIELD_LABELS[state.lang][f] || f;

try { const l = localStorage.getItem("va_lang"); if (l === "fr" || l === "en") state.lang = l; } catch (_) { /* storage unavailable */ }

/* ---------- API ---------- */
class ApiErr extends Error { constructor(status, body) { super(body?.error?.message || "error"); this.status = status; this.body = body?.error || {}; } }
async function api(path, opts = {}) {
  let res;
  try {
    res = await fetch(path, { credentials: "same-origin", ...opts, headers: { "Content-Type": "application/json", ...(opts.headers || {}) } });
  } catch (e) { throw new ApiErr(0, { error: { code: "network" } }); }
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiErr(res.status, body);
  return { body, headers: res.headers, status: res.status };
}
const get = async (p) => (await api(p)).body;
const send = async (p, method, data, headers) => (await api(p, { method, body: data === undefined ? undefined : JSON.stringify(data), headers })).body;

function errorText(e) {
  const b = e.body || {};
  if (e.status === 0) return t("err_network");
  if (b.code === "invalid_credentials") return t("err_credentials");
  if (b.code === "invalid_code") return t("err_code");
  if (b.code === "too_many_attempts") return t("err_too_many");
  if (b.code === "invite_invalid") return t("err_invite");
  if (b.code === "account_exists") return t("err_account_exists");
  if (b.rule) return t(`pw_${b.rule}`);
  if (e.status === 400 && b.field === "display_name") return t("err_name");
  if (e.status === 400 && (b.field === "email" || b.field === "password")) return t("err_fields");
  if (e.status === 401) return state.mode === "dev" ? t("err_401") : t("err_401_pw");
  if (e.status === 404) return t("err_404");
  if (e.status === 403) return b.required_plan ? t("err_403_plan", I18N[state.lang].plans[b.required_plan]) : (b.reason === "role_not_permitted" ? t("gate_role") : t("err_403"));
  if (e.status === 409 && b.code === "idempotency_conflict") return t("err_409_idem");
  if (e.status === 409 && b.code === "pursuit_exists") return t("err_pursuit_exists");
  if (e.status === 409 && b.code === "opportunity_closed") return t("err_closed");
  if (e.status === 409 && b.code === "already_published") return t("reject_blocked");
  if (e.status === 422) return b.message || t("err_422");
  if (e.status === 429) return t("err_429", b.limit, I18N[state.lang].plans[b.upgrade_plan] || b.upgrade_plan);
  if (e.status === 503) return t("err_503");
  if (e.status === 400 && b.message) return b.message;
  return b.message || t("err_generic");
}

/* ---------- Formatting ---------- */
const locale = () => (state.lang === "fr" ? "fr-SN" : "en-GB");
function fmtDate(iso, time = true) {
  if (!iso) return "—";
  const d = new Date(iso);
  const s = new Intl.DateTimeFormat(locale(), { timeZone: "UTC", day: "numeric", month: "long", year: "numeric", ...(time ? { hour: "2-digit", minute: "2-digit" } : {}) }).format(d);
  return time ? `${s} GMT` : s;
}
function daysLeft(iso) {
  const ms = new Date(iso) - new Date();
  if (ms <= 0) return t("closed");
  return t("days_left", Math.floor(ms / 86400000));
}
const money = (v) => (v && v.amount != null ? new Intl.NumberFormat(locale(), { style: "currency", currency: v.currency || "XOF", maximumFractionDigits: 0 }).format(v.amount) : "—");
function fmtValue(field, v) {
  if (v == null || v === "") return "—";
  if (field === "deadline") return fmtDate(v);
  if (field === "published_on") return fmtDate(v, false);
  if (field === "estimated_value") return money(v);
  if (field === "lots") return v.map((l) => `${t("lot")} ${l.number} — ${l.title} (${t("bid_security")} : ${money(l.bid_security)})`).join("; ");
  if (field === "capability_tags") return capList(v);
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return v.numero ? `${v.numero} — ${v.motif || ""} (${v.date || ""})` : JSON.stringify(v);
  return String(v);
}

/* ---------- Shell ---------- */
function announce(msg) { const l = $("#live"); l.textContent = ""; setTimeout(() => { l.textContent = msg; }, 30); }
function flash(kind, msg) { state.flash = { kind, msg }; }
function flashHtml() {
  if (!state.flash) return "";
  const f = state.flash; state.flash = null;
  return `<div class="notice notice-${f.kind}" role="${f.kind === "error" ? "alert" : "status"}">${esc(f.msg)}</div>`;
}
function setLang(l) {
  state.lang = l;
  try { localStorage.setItem("va_lang", l); } catch (_) { /* ignore */ }
  document.documentElement.lang = l;
  $("#lang-fr").setAttribute("aria-pressed", String(l === "fr"));
  $("#lang-en").setAttribute("aria-pressed", String(l === "en"));
  render();
}
function shell() {
  document.documentElement.lang = state.lang;
  document.querySelector(".skip-link").textContent = t("skip");
  $("#nav").setAttribute("aria-label", t("nav"));
  $("#env-banner").textContent = state.mode === "dev" ? t("env") : t("env_staging");
  $("#footer").textContent = state.mode === "dev" ? t("footer") : t("footer_staging");
  const me = state.me;
  const sw = $("#switch");
  if (!me) { $("#nav").innerHTML = ""; $("#who").textContent = ""; sw.hidden = true; return; }
  sw.hidden = false; sw.textContent = state.mode === "dev" ? t("switch") : t("sign_out");
  const plan = me.plan ? ` · ${I18N[state.lang].plans[me.plan]}` : "";
  $("#who").innerHTML = `${esc(t("signed_as"))} <strong>${esc(me.user.display_name)}</strong> · ${esc(me.organization.name)}${esc(plan)}`;
  const items = me.organization.kind === "customer"
    ? [["#/opportunities", t("nav_opps")], ["#/bids", t("nav_bids")], ["#/alerts", t("nav_alerts"), state.unread]]
    : me.role === "analyst"
      ? [["#/review", t("nav_review")], ["#/sources", t("nav_sources")], ["#/trace", t("nav_trace")]]
      : [["#/audit", t("nav_audit")], ["#/trace", t("nav_trace")]];
  const cur = location.hash.split("?")[0].split("/").slice(0, 2).join("/");
  $("#nav").innerHTML = `<ul>${items.map(([h, l, n]) => `<li><a href="${h}"${cur === h ? ' aria-current="page"' : ""}>${esc(l)}${n ? ` <span class="count" aria-label="${n} ${esc(t("unread"))}">${n}</span>` : ""}</a></li>`).join("")}</ul>`;
}
function view(html, title) {
  const m = $("#main");
  m.innerHTML = html;
  document.title = `${title} — VeraAfrika`;
  const h1 = m.querySelector("h1");
  if (h1) {
    h1.tabIndex = -1;
    // Move focus on in-app navigation only; on first load the skip link stays first in the tab order.
    if (state.navigated) h1.focus({ preventScroll: false });
  }
  state.navigated = true;
  scrollRegions();
}
/* Tables that scroll sideways must be reachable by keyboard (WCAG 2.1.1, axe scrollable-region-focusable). */
function scrollRegions() {
  document.querySelectorAll("main .table-wrap").forEach((w) => {
    const scrolls = w.scrollWidth > w.clientWidth + 1;
    if (scrolls) {
      w.tabIndex = 0; w.setAttribute("role", "region");
      const label = w.querySelector("caption")?.textContent || w.closest("section")?.querySelector("h2")?.textContent || document.querySelector("main h1")?.textContent || "";
      w.setAttribute("aria-label", label.trim());
    } else { w.removeAttribute("tabindex"); w.removeAttribute("role"); w.removeAttribute("aria-label"); }
  });
}
window.addEventListener("resize", () => { clearTimeout(scrollRegions.t); scrollRegions.t = setTimeout(scrollRegions, 150); });
const loadingView = () => { $("#main").innerHTML = `<p class="visually-hidden" role="status">${esc(t("loading"))}</p><div class="stack" aria-hidden="true"><div class="skeleton"></div><div class="skeleton"></div></div>`; };
const errorView = (e) => view(`<h1>${esc(t("err_generic").split(".")[0])}</h1><div class="notice notice-error" role="alert">${esc(errorText(e))}</div><p><a class="btn" href="#/">${esc(t("back"))}</a></p>`, "Error");

async function refreshMe() {
  state.mfaPending = false;
  try { state.me = await get("/v1/me/context"); } catch (e) {
    state.me = null;
    if (e.status === 401 && e.body?.code === "mfa_required") { state.mfaPending = true; return; }
    if (e.status !== 401) throw e;
  }
  if (state.me && state.me.organization.kind === "customer") {
    try { state.unread = (await get("/v1/alerts")).unread; } catch (_) { state.unread = 0; }
  }
}

/* ---------- Router ---------- */
const routes = [
  [/^#\/signin$/, signIn], [/^#\/mfa$/, mfaView], [/^#\/invite\/([\w-]+)$/, inviteView],
  [/^#\/opportunities$/, oppList], [/^#\/opportunities\/([\w-]+)$/, oppDetail],
  [/^#\/bids$/, bids], [/^#\/bids\/([\w-]+)$/, bidDetail], [/^#\/alerts$/, alerts],
  [/^#\/review$/, reviewQueue], [/^#\/review\/([\w-]+)$/, reviewTask], [/^#\/sources$/, sources],
  [/^#\/trace$/, traceList], [/^#\/trace\/([\w-]+)$/, traceView], [/^#\/audit$/, auditLog],
];
async function render() {
  shell();
  const hash = location.hash || "#/";
  const publicRoute = hash === "#/signin" || hash === "#/mfa" || hash.startsWith("#/invite/");
  if (!state.me && !publicRoute) { location.hash = "#/signin"; return; }
  if (hash === "#/" || hash === "") {
    location.hash = state.me.organization.kind === "customer" ? "#/opportunities" : state.me.role === "analyst" ? "#/review" : "#/audit";
    return;
  }
  for (const [re, fn] of routes) {
    const m = hash.split("?")[0].match(re);
    if (m) {
      loadingView();
      try { await fn(...m.slice(1)); } catch (e) {
        if (e.status === 401 && e.body.code === "mfa_required") { state.me = null; location.hash = "#/mfa"; return; }
        if (e.status === 401 && hash !== "#/signin" && !hash.startsWith("#/invite/") && hash !== "#/mfa") { state.me = null; flash("error", t("err_401")); location.hash = "#/signin"; return; }
        errorView(e);
      }
      shell();
      return;
    }
  }
  errorView(new ApiErr(404, {}));
}
window.addEventListener("hashchange", render);

/* ---------- Sign-in (development) ---------- */
async function afterAuth(out) {
  if (out.mfa) { state.mfa = out.mfa; location.hash = "#/mfa"; return; }
  await refreshMe();
  if (state.me?.user?.locale) setLangSilently(state.me.user.locale);
  location.hash = "#/";
  if (location.hash === "#/") render();
}
function pwField(id, auto, describedBy) {
  return `<div><label for="${id}">${esc(t("password"))}</label><input type="password" id="${id}" name="password" autocomplete="${auto}" required${describedBy ? ` aria-describedby="${describedBy}"` : ""}>
    <label style="font-weight:400;display:flex;gap:8px;align-items:center;min-height:44px;margin-top:4px"><input type="checkbox" data-show="${id}" style="width:20px;height:20px"> ${esc(t("show_pw"))}</label></div>`;
}
function wireShow() { $("#main").querySelectorAll("[data-show]").forEach((c) => c.addEventListener("change", () => { $("#" + c.dataset.show).type = c.checked ? "text" : "password"; })); }
function formError(form, e) {
  const box = form.querySelector("[data-err]"); box.textContent = errorText(e);
  const f = e.body?.field && form.querySelector(`[name="${e.body.field}"]`); (f || form.querySelector("input")).focus();
}
async function signIn() {
  if (state.mode !== "dev") {
    view(`<div class="card" style="max-width:480px;margin:0 auto"><h1>${esc(t("auth_title"))}</h1>${flashHtml()}
      <form id="login" class="stack" novalidate>
        <div><label for="li-email">${esc(t("email"))}</label><input type="text" inputmode="email" id="li-email" name="email" autocomplete="username" autocapitalize="none" spellcheck="false" required></div>
        ${pwField("li-pw", "current-password")}
        <div class="field-error" role="alert" data-err></div>
        <button class="btn btn-primary" type="submit">${esc(t("sign_in"))}</button>
        <p class="hint">${esc(t("signin_help"))}</p></form></div>`, t("auth_title"));
    wireShow();
    $("#login").addEventListener("submit", async (ev) => {
      ev.preventDefault(); const f = ev.target, b = f.querySelector("button[type=submit]"); b.setAttribute("aria-busy", "true");
      try { await afterAuth(await send("/v1/auth/login", "POST", { email: f.email.value.trim(), password: f.password.value })); }
      catch (e) { b.removeAttribute("aria-busy"); formError(f, e); }
    });
    return;
  }
  const { personas } = await get("/v1/dev/personas");
  view(`<h1>${esc(t("signin_title"))}</h1>${flashHtml()}<p>${esc(t("signin_intro"))}</p>
    <ul class="persona-list">${personas.map((p) => `<li><button type="button" class="btn" data-user="${esc(p.id)}">
      ${esc(p.display_name)}<span class="sub">${esc(p.organization)}</span>
      <span class="sub">${esc(I18N[state.lang].roles[p.role] || p.role)}${p.plan ? " · " + esc(I18N[state.lang].plans[p.plan]) : ""}</span></button></li>`).join("")}</ul>`, t("signin_title"));
  $("#main").querySelectorAll("[data-user]").forEach((b) => b.addEventListener("click", async () => {
    b.setAttribute("aria-busy", "true");
    try {
      await send("/v1/dev/sessions", "POST", { user_id: b.dataset.user });
      await refreshMe();
      if (state.me?.user?.locale) setLangSilently(state.me.user.locale);
      location.hash = "#/";
    } catch (e) { b.removeAttribute("aria-busy"); flash("error", errorText(e)); render(); }
  }));
}
function setLangSilently(l) {
  let stored = null; try { stored = localStorage.getItem("va_lang"); } catch (_) { /* ignore */ }
  if (!stored) { state.lang = l; $("#lang-fr").setAttribute("aria-pressed", String(l === "fr")); $("#lang-en").setAttribute("aria-pressed", String(l === "en")); }
}

async function mfaView() {
  let setup = null;
  if (state.mfa !== "verify") { try { setup = await get("/v1/auth/mfa/setup"); } catch (e) { if (e.body?.code !== "mfa_already_enabled") throw e; } }
  view(`<div class="card" style="max-width:560px;margin:0 auto"><h1>${esc(t("mfa_title"))}</h1>
    ${setup ? `<p>${esc(t("mfa_setup_intro"))}</p><ol><li><p>${esc(t("mfa_step1"))}</p><p><code style="font-size:1.1rem;letter-spacing:1px" id="mfa-key">${esc(setup.secret)}</code></p>
      <p><a href="${esc(setup.otpauth_uri)}">${esc(t("mfa_open_app"))}</a></p></li><li><p>${esc(t("mfa_step2"))}</p></li></ol>` : `<p>${esc(t("mfa_verify_intro"))}</p>`}
    <form id="mfa" class="stack" novalidate><div><label for="mfa-code">${esc(t("mfa_code"))}</label>
      <input type="text" id="mfa-code" name="code" inputmode="numeric" autocomplete="one-time-code" maxlength="7" required style="max-width:200px"></div>
      <div class="field-error" role="alert" data-err></div><button class="btn btn-primary" type="submit">${esc(t("verify"))}</button></form></div>`, t("mfa_title"));
  $("#mfa").addEventListener("submit", async (ev) => {
    ev.preventDefault(); const f = ev.target;
    try { await send("/v1/auth/mfa/verify", "POST", { code: f.code.value }); state.mfa = null; await afterAuth({}); }
    catch (e) { if (e.status === 401 && e.body.code !== "invalid_code") { location.hash = "#/signin"; return; } formError(f, e); }
  });
}
async function inviteView(token) {
  const inv = await get(`/v1/auth/invites/${token}`);
  const reset = inv.purpose === "reset";
  const title = reset ? t("reset_title") : t("invite_title");
  view(`<div class="card" style="max-width:520px;margin:0 auto"><h1>${esc(title)}</h1><p>${esc(reset ? t("reset_for", inv.email) : t("invite_for", inv.organization, inv.email))}</p>
    <form id="inv" class="stack" novalidate>
      <input type="text" name="username" autocomplete="username" value="${esc(inv.email)}" hidden readonly>
      ${reset ? "" : `<div><label for="iv-name">${esc(t("your_name"))}</label><input type="text" id="iv-name" name="display_name" autocomplete="name" required></div>`}
      ${pwField("iv-pw", "new-password", "iv-pw-rule")}<p class="hint" id="iv-pw-rule" style="margin-top:-8px">${esc(t("pw_rule"))}</p>
      ${reset ? "" : `<div><label for="iv-lang">${esc(t("language"))}</label><select id="iv-lang" name="locale"><option value="fr"${state.lang === "fr" ? " selected" : ""}>Français</option><option value="en"${state.lang === "en" ? " selected" : ""}>English</option></select></div>`}
      <div class="field-error" role="alert" data-err></div><button class="btn btn-primary" type="submit">${esc(reset ? t("save_password") : t("create_account"))}</button></form></div>`, title);
  wireShow();
  $("#inv").addEventListener("submit", async (ev) => {
    ev.preventDefault(); const f = ev.target, b = f.querySelector("button[type=submit]"); b.setAttribute("aria-busy", "true");
    try {
      const out = await send(`/v1/auth/invites/${token}/accept`, "POST", { display_name: f.display_name?.value || "", password: f.password.value, locale: f.locale?.value || state.lang });
      if (f.locale) setLang(f.locale.value);
      await afterAuth(out);
    } catch (e) { b.removeAttribute("aria-busy"); formError(f, e); }
  });
}

/* ---------- Customer: tenders ---------- */
let sectorsCache = null;
function statusBadges(o) {
  const b = [];
  if (o.sample_data) b.push(`<span class="badge badge-sample">${esc(t("sample"))}</span>`);
  if (o.amended) b.push(`<span class="badge badge-amended">${esc(t("amended"))}${o.last_amendment?.issuer_reference ? " · " + esc(o.last_amendment.issuer_reference) : ""}</span>`);
  b.push(o.verification === "issuer_amendment_pending_confirmation"
    ? `<span class="badge badge-pending">${esc(t("pending_confirm"))}</span>`
    : `<span class="badge badge-ok">${esc(t("reviewed"))}</span>`);
  return `<div class="badges">${b.join("")}</div>`;
}
async function oppList() {
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  const country = params.get("country") || "SN", q = params.get("q") || "", sector = params.get("sector") || "";
  if (!sectorsCache) sectorsCache = (await get("/v1/reference/sector-taxonomy?level=sector")).nodes;
  const qs = new URLSearchParams({ country, ...(q ? { q } : {}), ...(sector ? { industry_code: sector } : {}) });
  const data = await get(`/v1/opportunities?${qs}`);
  const cov = data.coverage;
  const covText = data.complete
    ? `<p class="hint">${esc(t("coverage_on", fmtDate(cov.last_success_at)))}</p>`
    : `<div class="notice notice-warning" role="status">${esc(t("coverage_off", cov.country_code, I18N[state.lang].states[cov.state] || cov.state))}</div>`;
  const list = data.results.length
    ? `<ul class="results">${data.results.map((o) => `<li class="card opp-card">
        <h2><a href="#/opportunities/${esc(o.id)}">${esc(o.title)}</a></h2>
        ${statusBadges(o)}
        <dl class="meta">
          <div><dt>${esc(t("deadline"))}</dt><dd>${esc(fmtDate(o.deadline))} · <strong>${esc(daysLeft(o.deadline))}</strong></dd></div>
          <div><dt>${esc(t("issuer"))}</dt><dd>${esc(o.issuer)}</dd></div>
          <div><dt>${esc(t("source"))}</dt><dd>${esc(o.source.name)} · ${esc(t("observed"))} ${esc(fmtDate(o.source.observed_at, false))}</dd></div>
        </dl></li>`).join("")}</ul>`
    : data.complete ? `<div class="notice notice-info" role="status">${esc(t("empty"))}</div>` : "";
  view(`<h1>${esc(t("opps_title"))}</h1>${flashHtml()}
    <form class="card filters" id="filters" role="search">
      <div><label for="f-q">${esc(t("search_label"))}</label><input type="search" id="f-q" name="q" value="${esc(q)}" aria-describedby="f-q-hint"><p class="hint" id="f-q-hint">${esc(t("search_hint"))}</p></div>
      <div><label for="f-country">${esc(t("country"))}</label><select id="f-country" name="country">${COUNTRIES.map(([c, fr, en]) => `<option value="${c}"${c === country ? " selected" : ""}>${esc(state.lang === "fr" ? fr : en)}</option>`).join("")}</select>
        <label for="f-sector" style="margin-top:8px">${esc(t("sector"))}</label><select id="f-sector" name="sector"><option value="">${esc(t("all_sectors"))}</option>${sectorsCache.map((s) => `<option value="${esc(s.code)}"${s.code === sector ? " selected" : ""}>${esc(s.label)}</option>`).join("")}</select></div>
      <div><button class="btn btn-dark" type="submit">${esc(t("apply"))}</button></div>
    </form>
    ${covText}
    <p role="status"><strong>${esc(t("results", data.results.length))}</strong></p>
    ${list}`, t("opps_title"));
  $("#filters").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const f = new FormData(ev.target);
    const p = new URLSearchParams(); for (const [k, v] of f) if (v) p.set(k, v);
    location.hash = `#/opportunities?${p}`;
  });
}

async function oppDetail(id) {
  const o = await get(`/v1/opportunities/${id}`);
  const la = o.last_amendment;
  const deadlineChange = o.amendment_history?.[0]?.changes?.find((c) => c.field === "deadline");
  const amendNote = la ? `<div class="amend-note" role="note"><strong>${esc(t("amend_note", la.issuer_reference, fmtDate(la.detected_at)))}</strong>
      ${deadlineChange ? `<br>${esc(t("previously"))} <del>${esc(fmtDate(deadlineChange.old))}</del>` : ""}</div>` : "";
  const ctaBlock = (() => {
    if (o.pursuit) return `<a class="btn btn-primary" href="#/bids/${esc(o.pursuit.id)}">${esc(t("open_bid"))}</a>`;
    if (o.access.pursuit) return `<button type="button" class="btn btn-primary" id="start-bid">${esc(t("start_bid"))}</button>`;
    const plan = state.me.plan === "discover";
    return `<div class="gate" role="note"><strong>${esc(plan ? t("gate_bid") : t("gate_role"))}</strong></div>`;
  })();
  const saveBtn = o.access.save ? `<button type="button" class="btn" id="save" aria-pressed="${o.saved}">${esc(o.saved ? t("saved") : t("save"))}</button>` : "";

  const details = o.access.details ? `
    <section class="card" aria-labelledby="h-sum"><h2 id="h-sum">${esc(t("summary"))}</h2>
      <dl class="meta" style="display:grid;gap:8px">
        <div><dt>${esc(t("reference"))}</dt><dd>${esc(o.reference)}</dd></div>
        <div><dt>${esc(t("procedure"))}</dt><dd>${esc(o.procedure)}</dd></div>
        <div><dt>${esc(t("place"))}</dt><dd>${esc(o.place)}</dd></div>
        <div><dt>${esc(t("value"))}</dt><dd>${esc(money(o.estimated_value))}</dd></div>
        <div><dt>${esc(t("industry"))}</dt><dd>${esc((o.industry || []).map((n) => n.label).join(" › "))}</dd></div>
        <div><dt>${esc(t("eligible_countries"))}</dt><dd>${esc((o.eligible_countries || []).join(", "))}</dd></div>
      </dl></section>
    <section class="card" aria-labelledby="h-lots"><h2 id="h-lots">${esc(t("lots"))}</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">${esc(t("lot"))}</th><th scope="col">${esc(t("summary"))}</th><th scope="col">${esc(t("bid_security"))}</th></tr></thead>
      <tbody>${(o.lots || []).map((l) => `<tr><td>${esc(l.number)}</td><td>${esc(l.title)}</td><td>${esc(money(l.bid_security))}</td></tr>`).join("")}</tbody></table></div></section>
    <section class="card" aria-labelledby="h-req"><h2 id="h-req">${esc(t("requirements"))}</h2><ul>${(o.qualification_requirements || []).map((r) => `<li>${esc(r)}</li>`).join("")}</ul></section>
    ${o.amendment_history?.length ? `<section class="card" aria-labelledby="h-hist"><h2 id="h-hist">${esc(t("history"))}</h2>
      <ul class="plain">${o.amendment_history.map((a) => `<li><strong>${esc(a.issuer_reference || "")}</strong> · ${esc(fmtDate(a.detected_at))}
        <ul>${a.changes.map((c) => `<li>${esc(fl(c.field))} : <del>${esc(fmtValue(c.field, c.old))}</del> → <strong>${esc(fmtValue(c.field, c.new))}</strong></li>`).join("")}</ul></li>`).join("")}</ul></section>` : ""}`
    : `<div class="gate" role="note"><strong>${esc(t("gate_details"))}</strong></div>`;

  const m = o.match;
  const matchBlock = m ? `<section class="card" aria-labelledby="h-match"><h2 id="h-match">${esc(t("match"))}</h2>
      <div class="badges"><span class="badge ${m.eligible ? "badge-ok" : "badge-high"}">${esc(m.eligible ? t("eligible") : t("not_eligible"))}</span>
      <span class="badge badge-muted">${esc(t("score"))} ${esc(m.score)}/100</span><span class="badge badge-muted">${esc(t("confidence"))} : ${esc(I18N[state.lang].conf[m.confidence])}</span></div>
      <h3>${esc(t("strengths"))}</h3><ul class="plain ticks">${m.strengths.map((s) => `<li>${esc(matchText(s))}</li>`).join("")}</ul>
      ${m.gaps.length ? `<h3 style="margin-top:12px">${esc(t("gaps"))}</h3><ul class="plain gaps">${m.gaps.map((s) => `<li>${esc(matchText(s))}</li>`).join("")}</ul>` : ""}
      <h3 style="margin-top:12px">${esc(t("limitations"))}</h3><ul>${m.limitations.map((s) => `<li>${esc(matchText(s))}</li>`).join("")}</ul>
      <p class="hint">${esc(t("rule_version", m.rule_version))}</p></section>` : "";

  const src = o.source;
  const sourceBlock = `<section class="card" aria-labelledby="h-src"><h2 id="h-src">${esc(t("source"))}</h2>
    <p><strong>${esc(src.name)}</strong><br>${esc(t("observed"))} ${esc(fmtDate(src.observed_at))}</p>
    <p class="hint">${esc(t("attribution"))} : ${esc(src.attribution)}</p>
    ${src.url ? `<p><a href="${esc(src.url)}" target="_blank" rel="noopener">${esc(t("open_source"))}<span class="visually-hidden"> (${state.lang === "fr" ? "nouvel onglet" : "opens in a new tab"})</span></a></p>
      <p class="hint">${esc(t("checksum"))} : <code>${esc(src.checksum.slice(0, 16))}…</code></p>` : `<div class="gate"><strong>${esc(t("gate_source"))}</strong></div>`}
  </section>`;

  view(`<p><a href="#/opportunities">← ${esc(t("back"))}</a></p>${flashHtml()}
    <h1>${esc(o.title)}</h1>
    <p>${esc(o.issuer)}</p>${statusBadges(o)}
    ${o.newer_source_version_under_review ? `<div class="notice notice-info" role="status">${esc(t("newer_review"))}</div>` : ""}
    <div class="grid-2 detail-grid" style="margin-top:16px">
      <aside class="stack side" aria-label="${esc(t("deadline"))}">
        <section class="card deadline" aria-labelledby="h-dl"><h2 id="h-dl">${esc(t("deadline"))}</h2>
          <p class="big">${esc(fmtDate(o.deadline))}</p><p class="remaining">${esc(daysLeft(o.deadline))}</p>${amendNote}
          <div class="actions" style="margin-top:16px">${ctaBlock}${saveBtn}</div></section>
        ${sourceBlock}
      </aside>
      <div class="stack primary">${details}${matchBlock}</div>
    </div>`, o.title);

  $("#save")?.addEventListener("click", async (ev) => {
    const b = ev.currentTarget, on = b.getAttribute("aria-pressed") !== "true";
    b.setAttribute("aria-busy", "true");
    try {
      await send(`/v1/opportunities/${id}/saved`, on ? "PUT" : "DELETE");
      b.setAttribute("aria-pressed", String(on)); b.textContent = on ? t("saved") : t("save");
      announce(on ? t("saved_msg") : t("unsaved_msg"));
    } catch (e) { announce(errorText(e)); alertInline(b, errorText(e)); } finally { b.removeAttribute("aria-busy"); }
  });
  $("#start-bid")?.addEventListener("click", (ev) => confirmBid(o, ev.currentTarget));
}
function alertInline(anchor, msg) {
  const n = document.createElement("div"); n.className = "notice notice-error"; n.setAttribute("role", "alert"); n.textContent = msg; n.style.marginTop = "12px";
  anchor.closest(".card, section, main").appendChild(n);
}

function confirmBid(o, trigger) {
  const d = $("#dialog");
  const key = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2)).replace(/[^\w-]/g, "");
  d.innerHTML = `<h2 id="dialog-title">${esc(t("confirm_title"))}</h2><p>${esc(t("confirm_body", fmtDate(o.deadline)))}</p>
    ${state.me.plan === "compete" ? `<p class="hint">${esc(t("confirm_limit"))}</p>` : ""}
    <div id="dialog-msg"></div>
    <div class="actions" style="margin-top:16px"><button type="button" class="btn btn-primary" id="d-ok">${esc(t("confirm"))}</button>
    <button type="button" class="btn" id="d-cancel">${esc(t("cancel"))}</button></div>`;
  d.showModal();
  $("#d-ok").focus();
  const close = () => { d.close(); trigger.focus(); };
  $("#d-cancel").addEventListener("click", close);
  d.addEventListener("cancel", (ev) => { ev.preventDefault(); close(); }, { once: true });
  $("#d-ok").addEventListener("click", async (ev) => {
    const b = ev.currentTarget; b.setAttribute("aria-busy", "true"); b.disabled = true;
    try {
      // The same key is reused on retry, so a lost response never creates a second bid.
      const p = await send(`/v1/opportunities/${o.id}/pursuits`, "POST", {}, { "Idempotency-Key": `ui-${key}` });
      d.close();
      flash("success", `${t("bid_started")}. ${t("bid_next")}`);
      location.hash = `#/bids/${p.id}`;
    } catch (e) {
      b.disabled = false; b.removeAttribute("aria-busy");
      b.textContent = e.status === 0 ? t("retry") : t("confirm");
      $("#dialog-msg").innerHTML = `<div class="notice notice-error" role="alert">${esc(errorText(e))}</div>`;
      if (e.status === 409 && e.body.pursuit_id) { d.close(); location.hash = `#/bids/${e.body.pursuit_id}`; }
    }
  });
}

/* ---------- Customer: bids, alerts ---------- */
async function bids() {
  const { pursuits } = await get("/v1/pursuits");
  view(`<h1>${esc(t("bids_title"))}</h1>${flashHtml()}${pursuits.length ? `<ul class="results">${pursuits.map((p) => `<li class="card opp-card">
      <h2><a href="#/bids/${esc(p.id)}">${esc(p.opportunity.title)}</a></h2>${statusBadges(p.opportunity)}
      <dl class="meta"><div><dt>${esc(t("deadline"))}</dt><dd>${esc(fmtDate(p.opportunity.deadline))} · <strong>${esc(daysLeft(p.opportunity.deadline))}</strong></dd></div>
      <div><dt>${esc(t("started_on"))}</dt><dd>${esc(fmtDate(p.created_at))}</dd></div></dl></li>`).join("")}</ul>`
    : `<div class="notice notice-info" role="status">${esc(t("bids_empty"))} <a href="#/opportunities">${esc(t("nav_opps"))}</a></div>`}`, t("bids_title"));
}
async function bidDetail(id) {
  const p = await get(`/v1/pursuits/${id}`);
  const o = p.opportunity;
  view(`<p><a href="#/bids">← ${esc(t("bids_title"))}</a></p>${flashHtml()}<h1>${esc(o.title)}</h1>${statusBadges(o)}
    <div class="grid-2"><section class="card" aria-labelledby="h-b"><h2 id="h-b">${esc(t("status"))} : ${esc(t("st_active"))}</h2>
      <p>${esc(t("started_on"))} ${esc(fmtDate(p.created_at))}</p><p class="hint">${esc(t("version_at_start", p.opportunity_version_at_start))}</p>
      ${o.version !== p.opportunity_version_at_start ? `<div class="amend-note" role="note"><strong>${esc(t("amend_note", o.last_amendment?.issuer_reference, fmtDate(o.last_amendment?.detected_at)))}</strong></div>` : ""}
      <p style="margin-top:12px">${esc(t("bid_next"))}</p><p><a class="btn" href="#/opportunities/${esc(o.id)}">${esc(t("nav_opps"))} : ${esc(o.reference || o.title)}</a></p></section>
      <section class="card deadline" aria-labelledby="h-d"><h2 id="h-d">${esc(t("deadline"))}</h2><p class="big">${esc(fmtDate(o.deadline))}</p><p class="remaining">${esc(daysLeft(o.deadline))}</p></section></div>`, o.title);
}
async function alerts() {
  const { alerts: list } = await get("/v1/alerts");
  const label = { deadline_changed: t("al_deadline"), pursuit_started: t("al_pursuit"), amendment_published: t("al_amend") };
  view(`<h1>${esc(t("alerts_title"))}</h1>${list.length ? `<ul class="results">${list.map((a) => {
      const ch = a.payload?.changes?.find((c) => c.field === "deadline");
      return `<li class="card"><h2>${esc(label[a.kind] || a.kind)}${a.issuer_reference ? " · " + esc(a.issuer_reference) : ""}</h2>
        ${ch ? `<p><del>${esc(fmtDate(ch.old))}</del> → <strong>${esc(fmtDate(ch.new))}</strong></p>` : ""}
        <p class="hint">${esc(fmtDate(a.created_at))} · ${esc(a.read_at ? t("read") : t("unread"))}</p>
        <div class="actions">${a.opportunity_id ? `<a class="btn" href="#/opportunities/${esc(a.opportunity_id)}">${esc(t("open"))}</a>` : ""}
        ${a.read_at ? "" : `<button type="button" class="btn-link" data-read="${esc(a.id)}">${esc(t("mark_read"))}</button>`}</div></li>`; }).join("")}</ul>`
    : `<div class="notice notice-info" role="status">${esc(t("alerts_empty"))}</div>`}`, t("alerts_title"));
  $("#main").querySelectorAll("[data-read]").forEach((b) => b.addEventListener("click", async () => {
    try { await send(`/v1/alerts/${b.dataset.read}/read`, "POST"); state.unread = Math.max(0, state.unread - 1); announce(t("read")); render(); }
    catch (e) { alertInline(b, errorText(e)); }
  }));
}

/* ---------- Analyst ---------- */
async function reviewQueue() {
  const { tasks } = await get("/v1/admin/review-tasks");
  view(`<h1>${esc(t("review_title"))}</h1>${flashHtml()}${tasks.length ? `<div class="table-wrap"><table><caption class="visually-hidden">${esc(t("review_title"))}</caption>
    <thead><tr><th scope="col">${esc(t("rv_priority"))}</th><th scope="col">${esc(t("rv_kind"))}</th><th scope="col">${esc(t("rv_notice"))}</th><th scope="col">${esc(t("rv_version"))}</th><th scope="col">${esc(t("rv_due"))}</th></tr></thead>
    <tbody>${tasks.map((x) => `<tr><td><span class="badge ${x.priority === "high" ? "badge-high" : "badge-muted"}">${esc(x.priority === "high" ? t("pr_high") : t("pr_normal"))}</span></td>
      <td>${esc(x.kind === "amendment" ? t("k_amend") : t("k_new"))}</td><td><a href="#/review/${esc(x.id)}">${esc(x.title || x.external_key)}</a><br><span class="hint">${esc(x.external_key)}</span></td>
      <td>${esc(x.version_no)}</td><td>${esc(fmtDate(x.due_at))}${x.overdue ? ` <span class="badge badge-high">${esc(t("overdue"))}</span>` : ""}</td></tr>`).join("")}</tbody></table></div>`
    : `<div class="notice notice-info" role="status">${esc(t("review_empty"))} <a href="#/sources">${esc(t("nav_sources"))}</a></div>`}`, t("review_title"));
}

async function reviewTask(id) {
  const d = await get(`/v1/admin/review-tasks/${id}`);
  const open = d.task.status === "open";
  const cur = Object.fromEntries(d.assertions.filter((a) => !a.superseded_by_id).map((a) => [a.field_path, a]));
  const rows = Object.keys(d.fields).sort().map((f) => {
    const a = cur[f];
    return `<tr><th scope="row">${esc(fl(f))}</th><td>${esc(fmtValue(f, d.fields[f]))}${a?.reason ? `<br><span class="hint">${esc(a.reason)}</span>` : ""}</td>
      <td><span class="badge ${a?.origin === "analyst" ? "badge-amended" : "badge-muted"}">${esc(a?.origin === "analyst" ? t("o_analyst") : t("o_source"))}</span></td>
      <td>${open && EDITABLE.includes(f) ? `<button type="button" class="btn-link" data-correct="${esc(f)}" aria-expanded="false" aria-controls="corr-${esc(f)}">${esc(t("correct"))}<span class="visually-hidden"> : ${esc(fl(f))}</span></button>` : ""}</td></tr>
      ${open && EDITABLE.includes(f) ? `<tr id="corr-${esc(f)}" hidden><td colspan="4"><form class="stack" data-form="${esc(f)}" novalidate>
        <div><label for="v-${esc(f)}">${esc(t("new_value"))} — ${esc(fl(f))}</label><input type="text" id="v-${esc(f)}" name="value" value="${esc(typeof d.fields[f] === "string" ? d.fields[f] : JSON.stringify(d.fields[f] ?? ""))}"></div>
        <div><label for="r-${esc(f)}">${esc(t("reason"))}</label><textarea id="r-${esc(f)}" name="reason" aria-describedby="rh-${esc(f)}" required></textarea><p class="hint" id="rh-${esc(f)}">${esc(t("reason_hint"))}</p></div>
        <div class="field-error" role="alert" data-err></div>
        <div class="actions"><button class="btn btn-dark" type="submit">${esc(t("save_corr"))}</button><button class="btn" type="button" data-cancel="${esc(f)}">${esc(t("cancel"))}</button></div></form></td></tr>` : ""}`;
  }).join("");
  const am = d.amendment;
  view(`<p><a href="#/review">← ${esc(t("review_title"))}</a></p>${flashHtml()}
    <h1>${esc(t("task_title"))} — ${esc(d.fields.reference || "")}</h1>
    <div class="badges"><span class="badge ${d.task.priority === "high" ? "badge-high" : "badge-muted"}">${esc(d.task.priority === "high" ? t("pr_high") : t("pr_normal"))}</span>
      <span class="badge badge-muted">${esc(d.task.kind === "amendment" ? t("k_amend") : t("k_new"))}</span><span class="badge badge-muted">${esc(t("version", d.version.version_no))}</span>
      ${d.version.review_state === "published_pending_confirmation" ? `<span class="badge badge-pending">${esc(t("pending_confirm"))}</span>` : ""}</div>
    ${am ? `<section class="card" aria-labelledby="h-am" style="margin-bottom:16px"><h2 id="h-am">${esc(t("amendment"))} · ${esc(am.issuer_reference || "")}</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">${esc(t("field"))}</th><th scope="col">${esc(t("old"))}</th><th scope="col">${esc(t("new"))}</th></tr></thead>
      <tbody>${am.changed_fields.map((c) => `<tr><th scope="row">${esc(fl(c.field))}</th><td>${esc(fmtValue(c.field, c.old))}</td><td><strong>${esc(fmtValue(c.field, c.new))}</strong></td></tr>`).join("")}</tbody></table></div></section>` : ""}
    <div class="split">
      <section class="card" aria-labelledby="h-ex"><h2 id="h-ex">${esc(t("extracted"))}</h2><div class="table-wrap"><table>
        <thead><tr><th scope="col">${esc(t("field"))}</th><th scope="col">${esc(t("value_col"))}</th><th scope="col">${esc(t("origin"))}</th><th scope="col"><span class="visually-hidden">${esc(t("correct"))}</span></th></tr></thead>
        <tbody>${rows}</tbody></table></div></section>
      <section class="card" aria-labelledby="h-raw"><h2 id="h-raw">${esc(t("raw"))}</h2>
        <p class="hint">${esc(t("retrieved"))} ${esc(fmtDate(d.source_record.retrieved_at))} · ${esc(t("checksum"))} <code>${esc(d.source_record.checksum.slice(0, 16))}…</code></p>
        <p><a href="${esc(d.source_record.source_url)}" target="_blank" rel="noopener">${esc(t("open_source"))}</a></p>
        <pre tabindex="0" aria-label="${esc(t("raw"))}">${esc(JSON.stringify(d.source_record.raw_json, null, 2))}</pre></section>
    </div>
    ${open ? `<section class="card" aria-labelledby="h-dec" style="margin-top:16px"><h2 id="h-dec">${esc(t("decision"))}</h2>
      <div><label for="note">${esc(t("approve_note"))} / ${esc(t("reject_note"))}</label><textarea id="note"></textarea></div><div id="dec-msg"></div>
      <div class="actions" style="margin-top:12px"><button type="button" class="btn btn-primary" id="approve">${esc(t("approve"))}</button>
      ${d.version.review_state === "published_pending_confirmation" ? `<p class="hint">${esc(t("reject_blocked"))}</p>` : `<button type="button" class="btn btn-danger" id="reject">${esc(t("reject"))}</button>`}</div></section>` : ""}
    <p style="margin-top:16px"><a href="#/trace/${esc(d.task.opportunity_id)}">${esc(t("nav_trace"))} →</a></p>`, t("task_title"));

  const main = $("#main");
  main.querySelectorAll("[data-correct]").forEach((b) => b.addEventListener("click", () => {
    const row = $(`#corr-${b.dataset.correct}`); const show = row.hidden; row.hidden = !show; b.setAttribute("aria-expanded", String(show));
    if (show) row.querySelector("input").focus();
  }));
  main.querySelectorAll("[data-cancel]").forEach((b) => b.addEventListener("click", () => {
    const f = b.dataset.cancel; $(`#corr-${f}`).hidden = true; const tr = main.querySelector(`[data-correct="${f}"]`); tr.setAttribute("aria-expanded", "false"); tr.focus();
  }));
  main.querySelectorAll("[data-form]").forEach((form) => form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = form.dataset.form, err = form.querySelector("[data-err]");
    const fd = new FormData(form); let value = fd.get("value");
    if (!String(fd.get("reason") || "").trim()) { err.textContent = t("reason_hint"); form.querySelector("textarea").focus(); return; }
    try { const j = JSON.parse(value); if (typeof j === "object") value = j; } catch (_) { /* plain string */ }
    try {
      await send(`/v1/admin/review-tasks/${id}/corrections`, "POST", { field: f, value, reason: fd.get("reason") });
      flash("success", t("corr_saved")); render();
    } catch (e) { err.textContent = errorText(e); form.querySelector("input").focus(); }
  }));
  $("#approve")?.addEventListener("click", async (ev) => {
    ev.currentTarget.setAttribute("aria-busy", "true");
    try { await send(`/v1/admin/review-tasks/${id}/approve`, "POST", { note: $("#note").value || null }); flash("success", t("approved_msg")); location.hash = "#/review"; }
    catch (e) { ev.currentTarget?.removeAttribute("aria-busy"); $("#dec-msg").innerHTML = `<div class="notice notice-error" role="alert">${esc(errorText(e))}</div>`; }
  });
  $("#reject")?.addEventListener("click", async () => {
    try { await send(`/v1/admin/review-tasks/${id}/reject`, "POST", { note: $("#note").value }); flash("success", t("rejected_msg")); location.hash = "#/review"; }
    catch (e) { $("#dec-msg").innerHTML = `<div class="notice notice-error" role="alert">${esc(errorText(e))}</div>`; $("#note").focus(); }
  });
}

async function sources() {
  const [{ sources: srcs }, { runs }] = await Promise.all([get("/v1/admin/sources"), get("/v1/admin/ingestion-runs")]);
  const rights = { approved: [t("rights_approved"), "badge-ok"], pending_review: [t("rights_pending"), "badge-pending"], denied: [t("rights_denied"), "badge-high"] };
  view(`<h1>${esc(t("sources_title"))}</h1>${flashHtml()}<div id="run-msg"></div>
    <ul class="results">${srcs.map((s) => `<li class="card"><h2>${esc(s.name)}</h2>
      <div class="badges"><span class="badge ${rights[s.rights_status][1]}">${esc(t("rights"))} : ${esc(rights[s.rights_status][0])}</span>${s.is_synthetic ? `<span class="badge badge-sample">${esc(t("sample"))}</span>` : ""}</div>
      <p class="hint">${esc(s.owner)} · ${esc(s.attribution)}</p>
      <div class="actions">${s.is_synthetic ? `<button type="button" class="btn btn-dark" data-run="${esc(s.key)}" data-snap="initial">${esc(t("run_initial"))}</button>
        <button type="button" class="btn" data-run="${esc(s.key)}" data-snap="amendment-1">${esc(t("run_amend"))}</button>`
        : `<button type="button" class="btn" data-run="${esc(s.key)}" data-snap="initial">${esc(t("run_candidate"))}</button>`}</div></li>`).join("")}</ul>
    <h2 style="margin-top:24px">${esc(t("runs"))}</h2>
    <div class="table-wrap"><table><thead><tr><th scope="col">${esc(t("r_started"))}</th><th scope="col">${esc(t("source"))}</th><th scope="col">${esc(t("r_status"))}</th><th scope="col">${esc(t("r_counts"))}</th><th scope="col">${esc(t("r_error"))}</th></tr></thead>
    <tbody>${runs.map((r) => `<tr><td>${esc(fmtDate(r.started_at))}</td><td>${esc(r.source_key)}</td><td><span class="badge ${r.status === "succeeded" ? "badge-ok" : r.status === "failed" ? "badge-high" : "badge-muted"}">${esc(I18N[state.lang].run_st[r.status] || r.status)}</span></td>
      <td>${esc(r.records_new)} / ${esc(r.records_amended)} / ${esc(r.records_unchanged)}</td><td>${esc(r.error || "—")}</td></tr>`).join("") || `<tr><td colspan="5">—</td></tr>`}</tbody></table></div>`, t("sources_title"));
  $("#main").querySelectorAll("[data-run]").forEach((b) => b.addEventListener("click", async () => {
    b.setAttribute("aria-busy", "true"); b.disabled = true;
    try { const r = await send(`/v1/admin/sources/${b.dataset.run}/runs`, "POST", { snapshot: b.dataset.snap }); flash("success", t("run_ok", r)); render(); }
    catch (e) {
      b.disabled = false; b.removeAttribute("aria-busy");
      const msg = e.body?.reason === "source_rights_not_approved" ? `${e.body.message} (${t("rights_pending")})` : errorText(e);
      $("#run-msg").innerHTML = `<div class="notice notice-error" role="alert">${esc(msg)}</div>`;
    }
  }));
}

async function traceList() {
  const { opportunities } = await get("/v1/admin/opportunities");
  view(`<h1>${esc(t("trace_title"))}</h1><p>${esc(t("trace_pick"))}</p>${opportunities.length ? `<ul class="results">${opportunities.map((o) => `<li class="card">
    <h2><a href="#/trace/${esc(o.id)}">${esc(o.title || o.external_key)}</a></h2><p class="hint">${esc(o.external_key)} · ${esc(t("version", o.latest_version))} · ${esc(o.status)}</p></li>`).join("")}</ul>`
    : `<div class="notice notice-info" role="status">—</div>`}`, t("trace_title"));
}

async function traceView(id) {
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  const field = params.get("field") || "deadline";
  const tr = await get(`/v1/admin/opportunities/${id}/trace${field ? `?field=${encodeURIComponent(field)}` : ""}`);
  const amendFor = (v) => tr.amendments.find((a) => a.to_version === v);
  view(`<p><a href="#/trace">← ${esc(t("trace_title"))}</a></p><h1>${esc(t("trace_title"))} — ${esc(fl(field))}</h1>
    <form class="card filters" id="tf"><div><label for="tf-field">${esc(t("trace_field"))}</label><select id="tf-field" name="field">
      ${Object.keys(FIELD_LABELS.en).map((f) => `<option value="${f}"${f === field ? " selected" : ""}>${esc(fl(f))}</option>`).join("")}</select></div><div></div>
      <div><button class="btn btn-dark" type="submit">${esc(t("apply"))}</button></div></form>
    <ol class="chain" style="margin-top:16px">${tr.versions.map((v) => {
      const a = amendFor(v.version_no);
      return `<li><h2>${esc(t("version", v.version_no))} <span class="badge badge-muted">${esc(I18N[state.lang].rev_st[v.review_state] || v.review_state)}</span>${tr.published_version === v.version_no ? ` <span class="badge badge-ok">${esc(t("published"))}</span>` : ""}</h2>
        ${a ? `<p class="amend-note"><strong>${esc(t("amendment"))} · ${esc(a.issuer_reference || "")}</strong> — ${esc(a.changed_fields.map((c) => fl(c.field)).join(", "))}</p>` : ""}
        <ul class="plain">${v.assertions.map((x) => `<li>${x.superseded_by_id ? "<del>" : "<strong>"}${esc(fmtValue(x.field_path, x.value_json))}${x.superseded_by_id ? "</del>" : "</strong>"}
          — <span class="badge ${x.origin === "analyst" ? "badge-amended" : "badge-muted"}">${esc(x.origin === "analyst" ? t("o_analyst") : t("o_source"))}</span>
          ${x.actor_name ? `${esc(t("by"))} ${esc(x.actor_name)}` : ""}${x.reason ? ` · ${esc(x.reason)}` : ""}${x.superseded_by_id ? ` · ${esc(t("superseded"))}` : ""}</li>`).join("") || "<li>—</li>"}</ul>
        <p class="hint">${esc(t("record"))} <code>${esc(v.source_record.id)}</code> · ${esc(t("checksum"))} <code>${esc(v.source_record.checksum.slice(0, 12))}…</code> · ${esc(t("retrieved"))} ${esc(fmtDate(v.source_record.retrieved_at))}
          · ${esc(t("run"))} <code>${esc(v.source_record.ingestion_run_id)}</code> (${esc(v.source_record.run_status)}) · <a href="${esc(v.source_record.source_url)}" target="_blank" rel="noopener">${esc(t("open_source"))}</a></p></li>`;
    }).join("")}</ol>`, t("trace_title"));
  $("#tf").addEventListener("submit", (ev) => { ev.preventDefault(); location.hash = `#/trace/${id}?field=${encodeURIComponent(new FormData(ev.target).get("field"))}`; });
}

async function auditLog() {
  const { events } = await get("/v1/audit/events?limit=200");
  view(`<h1>${esc(t("audit_title"))}</h1><div class="table-wrap"><table><caption class="visually-hidden">${esc(t("audit_title"))}</caption>
    <thead><tr><th scope="col">${esc(t("a_when"))}</th><th scope="col">${esc(t("a_action"))}</th><th scope="col">${esc(t("a_actor"))}</th><th scope="col">${esc(t("a_object"))}</th><th scope="col">${esc(t("details_col"))}</th></tr></thead>
    <tbody>${events.map((e) => `<tr><td>${esc(fmtDate(e.occurred_at))}</td><td><code>${esc(e.action)}</code></td><td>${esc(e.actor_id || t("system"))}<br><span class="hint">${esc(e.organization_id || "")}</span></td>
      <td>${esc(e.object_type || "")} <code>${esc(e.object_id || "")}</code></td><td><code>${esc(JSON.stringify(e.details_json))}</code></td></tr>`).join("")}</tbody></table></div>`, t("audit_title"));
}

/* ---------- Boot ---------- */
$("#lang-fr").addEventListener("click", () => setLang("fr"));
$("#lang-en").addEventListener("click", () => setLang("en"));
$("#switch").addEventListener("click", async () => {
  await send(state.mode === "dev" ? "/v1/dev/sign-out" : "/v1/auth/logout", "POST").catch(() => {});
  state.me = null; location.hash = "#/signin"; render();
});
(async () => {
  $("#lang-fr").setAttribute("aria-pressed", String(state.lang === "fr"));
  $("#lang-en").setAttribute("aria-pressed", String(state.lang === "en"));
  try { state.mode = (await get("/v1/auth/config")).mode; } catch (_) { state.mode = "password"; }
  try { await refreshMe(); } catch (_) { /* shown by render */ }
  if (state.mfaPending && !location.hash.startsWith("#/invite/")) { state.mfa = "verify"; location.hash = "#/mfa"; }
  render();
})();
