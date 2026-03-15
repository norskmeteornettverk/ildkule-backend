# Glossary

This glossary explains the main domain terms used in the project.
It starts from the PHP API in `api/` and is extended with terms from `fastapi_app/`.

## Suggested Home

Keep this file in `docs/glossary.md`.
Add a short link to it from the root `README.md` later.
This keeps the README short, while the glossary can grow with the project.

## Core Terms

`meteor`
A meteor event stored in the database. One meteor can have one or more observations from different stations and cameras.

`observation`
One camera record of a meteor. In code this is `ObservationCamData`.

`station`
A physical place that runs one or more cameras.

`cam`
One camera on a station, for example `cam1` or `cam4`.

`datetimetag`
A string made from the date folder and time folder, for example `20240512235404`. It works as a file-based meteor key.

`location`
A text value that tells where the meteor was seen or calculated to be.

## Frontend Terms

These terms come from the frontend UI text. They are listed here without depending on backend naming.

### Pages And Navigation

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| latest meteors | siste meteorer | siste registrerte meteorer |  | The main list view for recent meteors. |
| meteor filtering | meteorfiltrering | filter bar |  | The filter area above the meteor list. |
| year filter | velg år | year selection |  | A filter that limits the meteor list by year. |
| station filter | velg stasjon | station selection |  | A filter that limits the meteor list by station. |
| type filter | velg type | meteor class filter | krysspeilet, upeilet, meteorittkandidat | A filter that limits the meteor list by meteor class. |
| meteor search | søk i meteorer | søk |  | A text search in the meteor list. |
| loading state | laster inn | spinner |  | The loading message and spinner shown while the meteor list is being fetched. |
| empty state | ingen meteorer er lastet inn | no results |  | The message shown when no meteors are available in the list. |
| reset filters | nullstill | reset |  | An action that clears the current meteor filters. |
| load more | last inn flere | load more button |  | An action that loads more rows in a list. |
| meteor details | meteordetaljer | meteor page |  | The page that shows one meteor with media, path, and review actions. |
| report meteor | rapporter ny meteor | rapporter en meteor du har sett |  | The public page and form for sending in a sighting. |
| statistics dashboard | statistikk | dashboard |  | The page that shows counts and report tables. |
| user profile | brukerprofil | din profilside |  | The page where a user sees account data and own reviews. |
| login | innlogging | logg inn |  | The page or action used to sign in. |
| register | registrer deg | lag ny bruker |  | The page or action used to create an account. |
| forgot password | glemt passord | glemt passordet |  | The page used to request a password reset. |
| reset password | nullstill passord | oppdater passord |  | The page used to set a new password after reset. |
| about us | om oss | om ildkule.net, om Norsk Meteornettverk |  | A page with background and purpose for the site and network. |
| contact us | kontakt oss | kontaktskjema |  | The page with the public contact form. |
| partners | samarbeidspartnere |  | sponsorer, støttespillere | The page for partner, sponsor, and supporter names. |
| administration | administrasjon | admin area |  | The main admin menu in the frontend. |
| meteor administration | meteoradministrasjon | admin meteor list |  | The admin page for sorting, opening, and classifying meteors. |
| user administration | brukeradministrasjon | admin user list |  | The admin page for editing user role and user level. |
| station logs | stasjonslogger | stasjonslogg |  | The admin page that shows logs sent from stations. |

### Observation And Reporting

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteor | meteor | stjerneskudd |  | A meteor shown in lists, detail pages, and filters. |
| fireball | ildkule | bright meteor |  | A very bright meteor. This is the main public word in the report form and tutorial. |
| bolide | bolide | powerful fireball |  | A very strong fireball that may light up the ground or create shock effects. |
| meteorite | meteoritt |  |  | A piece that survives and reaches the ground. |
| meteorite fall | meteorittnedfall | nedfall |  | A possible fall of meteorite material to the ground. |
| meteorite candidate | meteorittkandidat |  |  | A meteor that may have a meteorite fall. |
| sighting | observasjon | sighting report |  | A visual report from a person who saw a meteor or fireball. |
| observation | observasjon | meteorobservasjon |  | A sighting or record of a meteor. |
| observation points | observasjonspunkter | camera observations |  | The station and camera records shown on the meteor detail page. |
| reported observation | innrapportert observasjon | rapportert meteor |  | A manual sighting sent in by a person. |
| observation time | observasjonstidspunkt | tidspunkt |  | The date and time when the sighting happened. |
| observed position | din posisjon | observatørens posisjon |  | The place where the person stood when the observation was made. |
| latitude | breddegrad | latitude |  | North-south position in the report form. |
| longitude | lengdegrad | longitude |  | East-west position in the report form. |
| first seen | først sett | start |  | The first visible point of the meteor in the report flow. |
| last seen | sist sett | slutt |  | The last visible point of the meteor in the report flow. |
| start coordinates | start-koordinater | start point |  | The map position for where the meteor seemed to start. |
| finish coordinates | slutt-koordinater | end point |  | The map position for where the meteor seemed to end. |
| bearing | himmelretning | kompassgrad |  | The direction from the observer to the meteor start or end point. |
| height | høyde | altitude |  | The visible height above the horizon in the report form. |
| dominant color | dominerende farge | color | hvit, grønn, blå, gul, orange, rød, annen, usikker | The main visible color of the meteor. |
| brightness | lysstyrke | light level | levels 1-6 | How bright the meteor looked to the observer. |
| duration | varighet | seconds | 1 sek to 10 sek | How long the meteor was visible. |
| comment | kommentarer | melding |  | Extra free-text information about the observation. |
| smoke trail | røykspor | trail in sky |  | A trail left behind after the meteor. |
| explosion | eksplosjon | smell, drønn |  | A strong sound or break-up event mentioned in the report text. |
| afterglow | etterglød | glow after event |  | Light that remains after the main meteor flash. |
| photo or video | foto/video | media |  | Extra evidence a user may mention in a report. |
| local time | lokaltid | local clock time |  | Local display time in the meteor views. |
| timestamp | tidspunkt | date and time |  | The date and time shown for a meteor in lists and detail views. |
| UTC | UTC | universal time |  | Stored or shown standard time in the meteor views. |
| unknown location | ukjent | no location |  | Used when a meteor has no visible place name. |
| main meteor image | bilde | meteor image |  | The main still image shown for a meteor in admin and detail views. |
| preview image | thumbnail | meteorbilde, meteor thumbnail |  | A smaller preview image used in meteor lists. |
| station fireball image | ildkulebilde | fireball image |  | A station-specific still image shown in the observation points table. |
| video | video | clip |  | A playable video shown for one observation in the meteor detail view. |
| trajectory map | kart | map.jpg |  | A generated map image for a meteor with calculated path data. |
| position-time graph | posisjon mot tid | posvstime graph |  | A graph image that shows meteor position over time. |
| speed-acceleration graph | hastighet og akselerasjon | spd_acc graph |  | A graph image that shows speed and acceleration. |
| orbital plot | bane rundt sola | orbit graph |  | A graph image that shows the meteor orbit. |
| height profile | høydegraf | height graph |  | A graph image that shows meteor height. |

### Tutorial And Sky Terms

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| tutorial checklist | sjekkliste | review checklist |  | The list of signs used to judge whether something looks like a fireball. |
| meteoroid | meteoroide |  |  | A small piece of stone or metal in space before it becomes a meteor. |
| micrometeoroid | mikrometeoroide |  |  | A very small meteoroid, often described as dust or a tiny grain. |
| straight-line motion | rett linje | straight path |  | A motion clue used in the tutorial to separate meteors from aircraft or lanterns. |
| clear weather | klarvær | clear sky |  | A sky condition used in the tutorial when light or shadows are easier to notice. |
| cloud cover | skydekke |  | tett skydekke | A sky condition that can hide a meteor from view. |
| terrain lighting | opplysning av terrenget | ground lighting |  | A sudden light on the ground caused by a bright fireball. |
| visible trail | lysende stripe eller flekk på himmelen | glowing trail |  | A bright stripe or patch that can remain in the sky after a fireball. |
| bang or boom | drønn eller smell | loud sound |  | A strong sound mentioned in the tutorial as a possible sign of a very bright event. |
| sonic boom | overlydssmell |  |  | A shock sound that can follow a powerful fireball. |
| shock wave | sjokkbølge |  |  | A strong pressure wave from a very powerful bolide. |
| apparent landing point | synes å lande | apparent fall point |  | The place where a fireball seems to land, even if the real fall is far away. |
| low entry angle | lav vinkel | shallow angle |  | A path angle that can make a meteor visible for a longer time. |

### Review And Classification

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteor review | meteorvurdering | vurdering, anbefaling |  | A user vote on whether something looks like a meteor. |
| ratings | vurderinger | review count | positive, negative | The total shown count of user votes on a meteor. |
| positive review count | positive vurderinger | thumbs up |  | The number of positive votes for a meteor. |
| negative review count | negative vurderinger | thumbs down |  | The number of negative votes for a meteor. |
| recommendation | anbefaling | review vote | ja, nei, nullstilt | The user's yes, no, or cleared choice for one meteor. |
| clear review | nullstill valg | tilbaketrukket anbefaling |  | A removed or reset user review. |
| manual classification | manuell bekreftelse av meteorobservasjon | klassifisering | bekreftet meteor, ikke en meteor, usikker | An admin choice for the final human classification. |
| confirmed meteor | bekreftet meteor | real meteor |  | An admin choice that says the event is a meteor. |
| not a meteor | ikke en meteor | rejected meteor |  | An admin choice that says the event is not a meteor. |
| unsure | usikker | unclear |  | An admin choice or status when the meteor is uncertain. |
| cross-station confirmed | krysspeilet | cross-checked meteor |  | A meteor with confirmation from more than one station. |
| unconfirmed | upeilet | not cross-station confirmed |  | A meteor without cross-station result data. |
| atmospheric path | atmosfærisk bane | bane |  | The calculated path section shown in the meteor detail view. |
| start height | starthøyde | start altitude |  | The first calculated height for the meteor path. |
| end height | slutthøyde | end altitude |  | The last calculated height for the meteor path. |
| meteor ID | meteor ID | meteor id |  | The visible identifier shown in admin meteor views. |

### User And Access

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| username | brukernavn | e-post |  | The login identity in the frontend. |
| password | passord | password |  | The secret used for login and reset. |
| user role | brukerrolle | rolle | ROLE_USER, ROLE_MOD, ROLE_ADMIN | The user's access role. |
| user level | brukernivå |  | lav, middels, høy | The user's review level in the frontend. |
| tutorial | meteorvurderingstutorial | sjekkliste |  | The guide that helps users understand how to review meteors. |
| tutorial completed | tutorial utført | gjennomført tutorial | ja, nei | A flag that shows whether the user finished the tutorial flow. |
| registered details | dine registrerte opplysninger | account details |  | The profile section with saved user data. |
| account confirmed | brukerkonto verifisert | bekreftet bruker | ja, nei | The state that says a user account is verified. |
| profile reviews | dine meteorvurderinger | own reviews |  | The profile section that lists the user's own review history. |
| information | informasjon | help text |  | The profile section that explains user levels. |

### Statistics And Admin Reports

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteors | meteorer | total meteors |  | A count of stored meteor events. |
| cross-station meteors | krysspeilede | confirmed meteors |  | A count of meteors with cross-station result data. |
| station statistics | stasjonstatistikk | station report |  | Statistics grouped by station. |
| camera statistics | kamerastatistikk | camera report |  | Statistics grouped by camera. |
| station name | stasjonsnavn | station |  | The station label used in tables and filters. |
| camera name | kameranavn | camera |  | The camera label used in statistics and detail views. |
| camera captures | kameraopptak | captures |  | The number of recorded camera events. |
| first observation time | ForsteObservasjonsTidspunkt | first seen in stats |  | The first recorded time in a statistics report. |
| last observation time | SisteObervasjonsTidspunkt | last seen in stats |  | The latest recorded time in a statistics report. |
| days with observations | DagerMedObservasjoner | active days |  | The number of days with records in a statistics report. |
| days since last observation | DagerSidenSisteObservasjon | days since last event |  | The number of days since the last record in a statistics report. |
| media coverage | medieomtale | press coverage |  | A dashboard card label for public media attention. |
| search action | leteaksjon | search campaign |  | A dashboard card label for search work after a meteor event. |
| meteorite find | meteorittfunn | recovered meteorite |  | A dashboard card label for a found meteorite. |

### Forms, Contact, And Legal

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| contact form | kontaktskjema | kontakt oss |  | The public form for direct messages to the network. |
| first name | fornavn | given name |  | A contact form field. |
| last name | etternavn | family name |  | A contact form field. |
| email | e-post | epost |  | A field used in contact, register, and password reset flows. |
| phone | telefon | tlf |  | A field used in the meteor report form. |
| privacy policy | personvernerklæring | privacy statement |  | The legal text about data handling. |
| terms of use | bruksvilkår | use conditions |  | The legal and privacy modal shown in the frontend. |
| cookies | informasjonskapsler | cookies |  | The browser storage term used in the legal text. |
| contact information | kontaktinformasjon | contact details |  | A section name in forms and legal text. |
| purpose | formål | purpose of network |  | A word used in the site and organization texts. |
| means or measures | virkemidler | methods |  | A word used in the organization text about how the network works. |
| sky monitoring | overvåkning av himmelen | camera monitoring |  | The activity of watching the sky with cameras. |
| search groups | letegrupper | recovery teams |  | Groups that search for meteorite falls. |

## Backend And API Terms

### Meteor Model And Review

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| camera confirmed | kamerabekreftet | camera_confirmed | 0, 1 | Shows if the meteor has cross-station result data such as `.res`, `.stat`, or `location.txt`. |
| cross-station confirmed | krysspeilet | cross_station_confirmed | 0, 1 | A clearer public name for the same domain idea as `camera_confirmed`. |
| user confirmed | brukerbekreftet | user_confirmed | -1, 0, 1 | The final human classification for a meteor. |
| user review | brukervurdering | user_review |  | One user's stored vote for one meteor. |
| classification | klassifisering |  | Positive, Negative, 1, 0 | The review or admin status given to a meteor. |
| confirmed | bekreftet |  |  | A shared word used in more than one place. For users it means account state. For meteor review it means the review value. |
| ratings | vurderinger | ratings |  | A total count of stored review votes. |
| positive ratings | positive vurderinger | positive_ratings |  | The number of positive reviews for a meteor. |
| negative ratings | negative vurderinger | negative_ratings |  | The number of negative reviews for a meteor. |
| track values | baneverdier | track_* |  | Calculated path values such as heights, speed, course, and start or end coordinates. |
| radiant values | radiantverdier | radiant_* |  | Calculated radiant values such as right ascension, declination, and shower. |
| fit error | tilpasningsfeil | fit_error |  | A value that describes how far the calculated fit is from the source data. |
| fit quality | tilpasningskvalitet | fit_quality |  | A value that describes how good the calculated fit is. |

### Observation And Raw Data

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| observation camera data | observasjonsdata fra kamera | observation_cam_data |  | One stored camera observation for a meteor. |
| trail values | sporverdier | trail_* |  | Per-observation trail data from `event.txt`, such as frames, timestamps, coordinates, and brightness. |
| video values | videodata | video_* |  | Video timing and video metadata from `event.txt`. |
| config values | konfigurasjonsdata | config_* |  | Detection settings from `event.txt`, such as thresholds, limits, and file paths. |
| summary values | sammendragsdata | summary_* |  | Summary values from `event.txt`, such as latitude, longitude, duration, and probability. |
| meteor res entry | rad fra res-fil | meteor_res_entry |  | One stored row from a `.res` file. |
| observation trail point | sporpunkt | observation_trail_point |  | One stored frame row from trail data in `event.txt`. |
| raw line | rålinje | raw_line |  | The original text from one `.res` line. |
| res entry count | antall res-rader | res_entry_count |  | The number of stored `.res` rows for one meteor. |
| trail point count | antall sporpunkter | trail_point_count |  | The number of stored frame rows for one observation. |
| res entries | res-rader | resEntries |  | The API response field with stored `.res` rows for one meteor. |
| trail points | sporpunkter | trailPoints |  | The API response field with stored frame rows for one observation. |

### Import, Identity, And Lifecycle

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteor load | meteorinnlasting | meteorload |  | The import step that reads meteor folders from disk and saves data to the database. |
| observation key | observasjonsnøkkel | observation_key |  | The stable key for one observation, based on station name, camera name, and event start time. |
| source hash | kildehash | source_hash | SHA-256 | A hash built from station name, camera name, `video_start`, `trail_timestamps`, and `trail_positions`. |
| event start utc | observasjonsstart i UTC | event_start_utc |  | The start time used to identify one observation. |
| upsert | oppdater eller opprett |  |  | Import behavior where an existing row is updated instead of duplicated. |
| first seen at | først sett | first_seen_at |  | The time when a meteor or observation was first imported. |
| last seen at | sist sett | last_seen_at |  | The time when a meteor or observation was last seen in an import run. |
| is deleted | er slettet | is_deleted | true, false | A soft-delete flag that keeps the row in the database. |
| deleted at | slettet tidspunkt | deleted_at |  | The time when the row was marked as deleted. |
| deletion reason | sletteårsak | deletion_reason | missing_from_import | The stored reason for a soft delete. |
| missing from import | mangler fra import | missing_from_import |  | Means the item was expected in the import window but was not found in the current run. |
| include deleted | inkluder slettede | includeDeleted | true, false | A query option that includes soft-deleted rows in API responses. |

### Import Files And Media

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| event file | event-fil | event.txt |  | The main observation file inside a station and camera folder. |
| location file | lokasjonsfil | location.txt |  | A one-line file with the meteor location after cross-station processing. |
| stat file | stat-fil | .stat |  | A calculated file with meteor values such as heights, speed, and radiant data. |
| res file | res-fil | .res |  | A calculated file with start and end coordinates and station result lines. |
| thumbnail image | miniatyrbilde | thumbnail.jpg |  | A smaller image made from `image.jpg` for list views. |

### Public API And Query Terms

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteor board | meteorboard | meteorboard |  | The admin list endpoint for meteors with more review detail. |
| insight report | innsiktsrapport | insight | total, station, cam, coordinates | Dashboard report endpoints for totals, stations, cameras, and coordinates. |
| report meteor | rapporter meteor | reportmeteor |  | The public API form for sending in a manual meteor report. |
| station log | stasjonslogg | stationlog |  | A log message sent from a meteor station to the API. |
| search term | søketerm | searchTerm |  | The text query used in `/meteors`. |
| station name query | stasjonsnavn | stationName |  | The station filter query in `/meteors`. |
| year query | år | year |  | The year filter query in `/meteors`. |
| meteor class query | meteorklasse | meteorClass | krysspeilet, upeilet, meteorittkandidat | The meteor class filter query in `/meteors`. |
| page | side | page | 1, 2, 3... | The page number used in list endpoints. |
| limit | grense | limit |  | The maximum number of rows returned by a list endpoint. |
| order by | sorter etter | orderby | date, ratings, crossbearing | The field name used for sorting. |
| order | rekkefølge | order | asc, desc | The sort direction used in list endpoints. |
| offset | startposisjon | offset | 0, 1, 2... | The starting row used in raw data list endpoints. |

### User And Auth API Terms

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| role | rolle | role | ROLE_USER, ROLE_MOD, ROLE_ADMIN | The main user role. |
| user role | brukerrolle | user_role |  | A public API alias for `role`. |
| roles | roller | roles |  | The public API list form of `role`. |
| user level | brukernivå | user_level | 0, 1, 2 | The stored user level used for workflow and access. |
| tutorial completed | tutorial fullført | tutorial_completed | true, false | Shows if a user has finished the tutorial flow. |
| tutorial complete | fullfør tutorial | tutorialComplete | true, false | The request field used when the API updates `tutorial_completed`. |
| confirm token | bekreftelsestoken | confirm_token |  | A token used when a new user confirms an account. |
| password reset token | passordreset-token | password_reset_token |  | A token used to reset a password. |
| password reset id | passordreset-id | passwordResetId |  | The public API field used when a password reset is confirmed. |
| token | token | token | JWT | The login token returned by the API. |
| access token | tilgangstoken | accessToken | JWT | A public API alias for the login token. |

### Filter And Class Terms

| English name | Norwegian name | Aliases | Common values | Description |
| --- | --- | --- | --- | --- |
| meteorite candidate | meteorittkandidat |  |  | A meteor with a low enough end height to be interesting for possible meteorite fall. |
| cross-station solved | krysspeilet |  |  | A meteor with cross-station calculated data. |
| unsolved | upeilet |  |  | A meteor without cross-station calculated data. |
