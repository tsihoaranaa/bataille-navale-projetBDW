# Auteurs : GERGES Robin, RAONIMANANA Aaron

# Contrôleur pour la déconnexion : réinitialise la session et redirige vers l'accueil
SESSION['joueur'] = None
REQUEST_VARS['redirect'] = '/accueil'