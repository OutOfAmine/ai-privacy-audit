---
name: ai-privacy-audit
description: Audite une codebase pour les risques données personnelles liés à l'IA — données personnelles (PII) envoyées aux API LLM (OpenAI, Anthropic, Mistral, Gemini, Azure OpenAI, Bedrock, Ollama…), prompt injection, RAG / recherche vectorielle sans contrôle d'accès, prompts et réponses stockés dans les logs, clés API en clair. Produit un rapport fichier:ligne avec gravité et correctif. Utilise ce skill dès que l'utilisateur parle d'audit RGPD/GDPR d'une app IA, de fuite de données vers un LLM, de sécurité d'un chatbot ou d'un RAG, de prompt injection, de "privacy review" ou "AI security audit" d'un repo, ou demande si son code envoie des données clients/personnelles à une IA — même sans dire "audit".
---

# Audit données personnelles × IA d'une codebase

But : trouver dans le code les endroits où des données personnelles peuvent fuiter via une IA, et dire comment corriger. Le rapport doit être actionnable : chaque constat pointe un `fichier:ligne` réel, lu et vérifié — pas une liste de risques théoriques.

## Démarche

### 1. Cartographier les points de contact IA

Trouver tous les appels à un modèle. Chercher (Grep, insensible à la casse) :

- SDK / imports : `openai`, `anthropic`, `@anthropic-ai`, `mistralai`, `google.generativeai`, `@google/genai`, `vertexai`, `cohere`, `ollama`, `bedrock-runtime`, `azure.ai.openai`, `langchain`, `llama_index`, `@ai-sdk`, `ai/` (Vercel AI SDK), `transformers`, `litellm`
- Appels HTTP directs : `api.openai.com`, `api.anthropic.com`, `api.mistral.ai`, `generativelanguage.googleapis.com`, `/v1/chat/completions`, `/v1/messages`
- Méthodes : `chat.completions.create`, `messages.create`, `generateText`, `streamText`, `invoke(`, `.predict(`, `embeddings.create`, `embed(`
- Vector stores : `pinecone`, `weaviate`, `qdrant`, `chroma`, `pgvector`, `milvus`, `faiss`, `similarity_search`, `vectorStore`

Pour chaque appel trouvé, **lire la fonction entière et remonter d'où viennent les données** du prompt (paramètre de requête HTTP, ligne de base de données, fichier uploadé…). C'est ce traçage qui distingue un vrai constat d'un faux positif : un `messages.create` avec une constante n'est pas un risque, le même appel avec `user.email` l'est.

Si aucun point de contact IA n'existe, le dire clairement et s'arrêter (vérifier quand même les clés API, étape 6).

### 2. Données personnelles envoyées au modèle

Pour chaque prompt, identifier ce qui y entre :

- Champs PII directs : nom, prénom, email, téléphone, adresse, date de naissance, IBAN, n° sécu / NIR, n° de carte, IP, géolocalisation, identifiants.
- Données sensibles art. 9 RGPD (gravité haute) : santé, opinions, religion, orientation, biométrie, données syndicales.
- Objets entiers sérialisés : `JSON.stringify(user)`, `str(customer)`, `f"{row}"`, `model_dump()` — envoie souvent plus que nécessaire.
- Contenu libre utilisateur (messages, tickets, documents uploadés) : peut contenir de la PII même si le code ne le "sait" pas.

Vérifier les protections : masquage / pseudonymisation avant envoi (ex. Presidio, regex de redaction), sélection explicite des champs, fournisseur configuré en zero-retention / hébergement UE (souvent invisible dans le code — le signaler comme point à vérifier hors code, pas comme faille).

### 3. Prompt injection

Risque réel quand du contenu non fiable (saisie utilisateur, page web, email, document, résultat d'outil) entre dans le prompt **et** que le modèle a du pouvoir :

- Concaténation directe dans le prompt système : `system: "... " + userInput`, f-string, template sans séparation.
- Contenu externe injecté sans délimitation (pages scrapées, emails, PDF, résultats RAG).
- Le modèle a des outils / function calling / agents : requêtes SQL, envoi d'email, HTTP, accès fichiers, exécution de code. Gravité = ce que l'outil permet de faire.
- Sortie du modèle exécutée ou rendue sans contrôle : `eval`, `exec`, SQL construit depuis la réponse, HTML rendu via `innerHTML` / `dangerouslySetInnerHTML` / `v-html` / `|safe`, commandes shell.

Un chatbot sans outils ni données privées dans son contexte = risque faible (au pire il dit des bêtises). Un agent avec accès DB clients et entrée utilisateur libre = critique. Calibrer la gravité sur l'impact, pas sur la simple présence de concaténation.

### 4. RAG / recherche vectorielle sans contrôle d'accès

- La requête au vector store filtre-t-elle par utilisateur / tenant / droits (`filter`, `namespace`, `where`, metadata `tenant_id`, `user_id`, ACL) ?
- Les documents de tous les clients sont-ils dans le même index sans métadonnée de propriétaire ?
- Le filtre vient-il du serveur (session authentifiée) ou d'un paramètre client modifiable ?
- Les documents indexés contiennent-ils de la PII (CV, contrats, tickets support) ?
- Droit à l'effacement : existe-t-il un chemin pour supprimer les embeddings d'un utilisateur ?

Absence de filtre sur un index multi-utilisateur = haute ou critique.

### 5. Logs, stockage et télémétrie des prompts

- Prompts / réponses complets loggés : `console.log(prompt)`, `logger.info(messages)`, `print(response)`, logs de debug laissés actifs.
- Outils d'observabilité LLM : LangSmith, Langfuse, Helicone, Datadog LLM, Sentry (breadcrumbs avec body de requête), OpenTelemetry — vérifier s'ils capturent les contenus et où ils sont hébergés.
- Historique de conversations stocké en base : durée de rétention, chiffrement, purge.
- Caches (Redis, fichiers) contenant prompts ou réponses.

### 6. Secrets et configuration

- Clés API en clair dans le code ou commitées (`sk-`, `sk-ant-`, `AIza`, fichiers `.env` versionnés — vérifier `.gitignore`).
- Clé API exposée côté client (bundle frontend, `NEXT_PUBLIC_*`, `VITE_*`, app mobile) : n'importe qui peut l'extraire.
- Appel IA fait directement depuis le navigateur avec des données d'autres utilisateurs.

Ne jamais recopier la valeur d'un secret dans le rapport : indiquer seulement fichier:ligne et le type de clé.

## Gravité

- **Critique** : fuite exploitable maintenant par un tiers (clé exposée côté client, RAG multi-tenant sans filtre, agent avec outils dangereux + entrée non fiable, sortie LLM exécutée).
- **Haute** : PII sensible (art. 9, financière, NIR) envoyée sans masquage ; prompts avec PII loggés en clair ; objets utilisateur complets envoyés.
- **Moyenne** : PII ordinaire envoyée sans minimisation ; injection possible mais impact limité ; rétention non définie.
- **Basse** : bonne pratique manquante sans exposition directe.
- **À vérifier hors code** : contrat fournisseur (no-training, DPA, région), configuration console.

## Rapport

Rédiger dans la langue de l'utilisateur. Utiliser ce format :

```markdown
# Audit données personnelles × IA — <nom du projet>

## Résumé
<2-4 phrases : combien de points de contact IA, nombre de constats par gravité, le risque principal.>

## Points de contact IA
| Fichier:ligne | Fournisseur / SDK | Données envoyées | Outils / actions |
|---|---|---|---|

## Constats
### [CRITIQUE] <titre court>
- **Où** : `chemin/fichier.ext:42`
- **Problème** : <ce qui se passe, avec le flux de données : source → prompt>
- **Scénario** : <comment ça fuit ou est exploité, concrètement>
- **Correctif** : <changement précis, extrait de code si utile>

(trier par gravité décroissante)

## À vérifier hors code
- <contrat fournisseur, rétention, région, DPA…>

## Ce qui est bien fait
- <protections déjà en place — utile pour ne pas les casser>
```

Rester factuel : si un constat dépend d'une hypothèse (ex. "si ce champ contient des données de santé"), le dire. Mieux vaut 5 constats vérifiés que 30 génériques. Ne pas modifier le code pendant l'audit — proposer les correctifs, l'utilisateur décide.
