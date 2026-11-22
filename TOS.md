# Terms of Service (TOS)

**FractalLauncher** — published by **FractalLabs**

*Effective date: October 22, 2026 · Version 1.0 · Contact: contact@FractalLauncher.dev*

---

**IMPORTANT — READ CAREFULLY.** These Terms of Service ("Terms", "TOS") govern your use of **FractalLauncher v1.2.4 (Optimize Patch)** and later versions, and all features, content and third-party integrations it provides ("the Service"),
published by **FractalLabs** ("FractalLabs", "we", "us", "our").

Your use of the Software is also governed by our [End User License Agreement (EULA)](EULA.md). Capitalized
terms not defined here have the meaning given in the EULA.

**By downloading, installing or using FractalLauncher you agree to be bound by these Terms and the EULA. If
you do not agree, do not use the Software — delete it and all of its components.**

---

## 1. Acceptance of Terms

1.1 These Terms form a binding agreement between you and FractalLabs.

1.2 You represent that you have the legal capacity to enter into these Terms in your jurisdiction. If you act
on behalf of an organization, you represent that you have authority to bind that organization.

1.3 **Continued use after an updated version of these Terms is published constitutes acceptance of the
updated Terms** (see §14).

## 2. Description of the Service

2.1 FractalLauncher is a **local, desktop Minecraft launcher**. It provides, among other features:

- launching Minecraft (vanilla and modded) with an included bundled Java runtime;
- profile and account management (Microsoft and offline accounts);
- mod, shader and resource-pack browsing and installation (via Modrinth);
- mod-loader installation (Fabric, Quilt, Forge, NeoForge) from official repositories;
- skin/cape preview and management, screenshots, world backups, a game console and diagnostics;
- AI-generated color themes (bring-your-own-key, see §6);
- a local server-ping feature for latency checks.

2.2 **FractalLabs operates no backend servers.** The Software runs entirely on your device. The only servers
your device contacts are **third-party services** (§5) and loopback addresses on your own machine
(`127.0.0.1`). There is no "FractalLabs account system" — local profiles are not FractalLabs accounts.

2.3 The Software is provided **free of charge**. FractalLabs reserves the right, in the future, to introduce
fees for certain features with prior notice; features in use at that time will remain available for a
reasonable transition period.

2.4 **The Service is provided on an "as is" and "as available" basis.** We do not guarantee any feature,
uptime, compatibility with every Minecraft version/mod/server, or continued availability of any integration.

## 3. Accounts and Authentication

### 3.1 Microsoft accounts

3.1.1 Microsoft sign-in uses the standard OAuth 2.0 authorization-code flow (with PKCE) using a publicly
available client registration. The authentication exchange happens **directly between your device and
Microsoft** (`login.microsoftonline.com`, `login.live.com`, Xbox Live and `api.minecraftservices.com`).

3.1.2 **Your credentials are never provided to FractalLabs.** We never see, request, transmit or store your
Microsoft password.

3.1.3 Access tokens and refresh tokens obtained through the flow are stored **locally on your device** in a
plain-text file (`~/.FractalLauncher/profiles.json`). **You acknowledge this storage method** and accept all
risk arising from it: anyone with access to your user account or device files may be able to read those
tokens. You are responsible for securing your device (login password, disk encryption, file permissions).

3.1.4 You are responsible for all activity performed with your Microsoft/Minecraft account through the
Software, and for keeping your Microsoft account secure.

3.1.5 You must comply with the **Microsoft Services Agreement**, the **Xbox terms**, and the **Minecraft End
User License Agreement** when using Microsoft sign-in. FractalLabs is not affiliated with Microsoft or Mojang
(EULA §5).

### 3.2 Offline accounts

3.2.1 The Software can create **offline accounts** — local, unofficial profiles with a generated (fake) UUID
and a fixed dummy token. They are **not** Mojang/Microsoft accounts and are not registered with Mojang.

3.2.2 Offline accounts provide access to single-player and to servers that explicitly permit offline/cracked
logins. They **do not** grant access to Realms, official online-mode servers, or authenticated services.

3.2.3 **Whether offline-mode play is acceptable is entirely your responsibility.** Many servers and services
prohibit it; some jurisdictions or contexts may implicate the Minecraft EULA. FractalLabs does not
encourage, endorse or take responsibility for any use of offline mode that violates a server's rules, the
Minecraft EULA, or applicable law. If a server bans offline accounts, or Microsoft restricts your account,
FractalLabs is not responsible.

### 3.3 Local profiles are yours to manage

3.3.1 All profiles are stored locally. Deleting `~/.FractalLauncher/` removes them permanently, including
tokens — FractalLabs cannot recover them. Use the built-in backups feature (or your own copies) for game
saves.

## 4. Offline Mode, Bans, and Game Integrity

4.1 The Software may launch Minecraft with modified JVM arguments, a bundled Java runtime, an authlib-injector
agent, and (at your request) local performance/mod configuration files.

4.2 **Anti-cheat and server policy are your responsibility.** Launching the game through FractalLauncher does
not make any mod, resource pack, JVM flag or account type permissible on any given server. Some servers or
services (e.g., Hypixel and other anti-cheat-protected networks) restrict mods, boosters, or account types;
violating their rules can result in bans **for which FractalLabs bears no responsibility**.

4.3 The diagnostics feature may recommend actions (e.g., deleting a conflicting `opengl32.dll`). Acting on
diagnostics output is at your own risk; review changes before applying them.

4.4 **Worlds, saves, screenshots and backups.** Although the Software includes a backup feature, you are
responsible for your own data. FractalLabs is not liable for corrupted, lost or inaccessible game saves,
worlds, mods, screenshots or backups (EULA §10).

## 5. Third-Party Services

5.1 The Software interacts with third-party services, including:

| Provider | Purpose | Terms |
|---|---|---|
| **Microsoft / Xbox / Minecraft Services** | Login, token refresh, entitlements | Microsoft Services Agreement, Xbox terms, Minecraft EULA |
| **Mojang** (`sessionserver.mojang.com`, `api.mojang.com`) | Profiles, skins, UUIDs | Mojang/Minecraft terms |
| **Modrinth** (`api.modrinth.com`) | Mod / shader / resource-pack search & downloads | Modrinth Terms of Service |
| **Cerebras** (`api.cerebras.ai`) | AI theme generation (BYOK) | Cerebras Terms / Privacy Policy |
| **Fabric, Quilt, Forge, NeoForge repositories** | Mod-loader installers | Their respective licenses/terms |
| **Minecraft server operators** (any server you ping or join) | Multiplayer | Each server's own rules |

5.2 **These services are governed by their own terms and privacy policies, which prevail over these Terms
for their respective services.** FractalLabs has no control over their availability, content, pricing or
policies, and is not responsible for outages, changes, terminations, bans or any other acts of these third
parties.

5.3 It is your responsibility to review and comply with all applicable third-party terms.

## 6. AI Theme Generation (Bring-Your-Own-Key)

6.1 The Software can generate color palettes from a text description using a **third-party large-language-model
API (Cerebras)**. This feature is **optional** and requires **your own API key** ("BYOK").

6.2 **Obtaining the key:** you must register with the AI provider yourself and obtain an API key under **their**
terms. FractalLabs is not affiliated with the AI provider and receives no revenue, share, or data from your
key.

6.3 **Your key stays on your device.** It is stored locally (default: `~/.FractalLauncher/cerebras_api_key.txt`,
plain text — you acknowledge this storage method and its risks). The key is transmitted **only** to the AI
provider's official API endpoint when you request theme generation.

6.4 **Prompts go to the AI provider.** Any description you type for theme generation is sent to the AI
provider, together with your API key, subject to **their** privacy policy and terms. Do not send personal,
confidential or sensitive information in prompts.

6.5 **AI output is provided as-is.** Generated palettes may be inaccurate, unattractive, or unsuitable.
FractalLabs does not review, endorse or warrant any AI output. You are responsible for evaluating generated
themes before use.

6.6 **Compliance with the AI provider's terms** (rate limits, prohibited uses, content policies) is your
responsibility. Abuse of your key or of the provider's API is between you and the provider.

6.7 FractalLabs may change or remove the AI integration at any time (e.g., if the provider's API changes).

## 7. Mods, Shaders, Resource Packs and Loader Installers

7.1 The Software lets you search, download and install modifications (collectively, "Mods") from **Modrinth**
and install mod loaders from their **official repositories**.

7.2 **Mods belong to their authors.** FractalLabs does not create, host, own or endorse Mods distributed
through the Software. Each Mod is subject to its own license and terms; **you must review and comply with
each Mod's license** before installing or redistributing it.

7.3 **Modrinth content rules apply.** Downloads are served from Modrinth under Modrinth's terms of service.
FractalLabs merely provides a client for Modrinth's public API.

7.4 **No piracy.** The Software is not designed to bypass payment, licensing or authentication for premium or
paid Mods, and must not be used to obtain paid content without authorization. Any attempt to do so violates
these Terms and may violate applicable law.

7.5 **Mod safety is your responsibility.** Mods are executable code. FractalLabs does not scan, verify,
virus-check or approve Mods. Install Mods only from sources you trust; use Modrinth's moderation signals
(download counts, verified status) at your own discretion.

7.6 **Mod compatibility and world safety.** Removing or adding Mods can corrupt saves or crash the game.
Back up your worlds before changing Mod sets. FractalLabs is not liable for damaged saves or lost Mod
configurations (EULA §10).

7.7 **Loader installers** (Fabric / Quilt / Forge / NeoForge) are downloaded from the projects' official Maven
repositories and executed on your machine using your configured Java runtime — standard behavior for these
installers. This execution happens with your implicit consent each time an install is requested.

## 8. Acceptable Use

You agree **not** to use the Software to:

1. **Violate any law** or third-party right (including intellectual-property, privacy, export-control and
   sanctions laws).
2. **Distribute malware** — use the Software to create, distribute, or spread viruses, trojans, ransomware,
   spyware or any malicious code.
3. **Circumvent authentication or entitlements** — bypass Microsoft/Mojang authentication, paywalls, license
   checks, or access content you are not authorized to access.
4. **Abuse third-party APIs** — scrape, spam, overload or automate excessive requests against Modrinth,
   Microsoft, Mojang, Cerebras or any other service beyond what the Software's normal features do.
5. **Abuse the server-ping feature** — use it to flood, DDoS, or stress any server, or to scan networks. The
   ping feature sends a single status request per click; it must not be weaponized.
6. **Impersonate or deceive** — misrepresent the Software's origin, rebrand it as your own commercial
   product without permission (EULA §3), or use generated themes/content to facilitate fraud.
7. **Exploit other users** — harass, threaten, defame, or harm others through any feature of the Software
   (e.g., sharing malicious server IPs, malicious resource packs/screenshots).
8. **Circumvent these Terms** — interfere with the Software's operation, attempt unauthorized access to
   FractalLabs systems (if any), or probe for vulnerabilities.
9. **Resell the Service** — use the free Software as the basis of a paid hosting, boosting, or automation
   service without our written consent.

Violation of this section terminates your license (EULA §8) and may give rise to civil or criminal liability.

## 9. Local Data, Privacy and Telemetry

9.1 **Everything stays on your device.** FractalLabs **operates no servers** and **collects no telemetry**.
The Software does not phone home to FractalLabs. No analytics, tracking, crash-reporting or usage-data
transmission to FractalLabs exists in the Software.

9.2 **What is stored locally** (all inside `~/.FractalLauncher/` on Windows):

| Data | File | Sensitivity |
|---|---|---|
| Accounts & tokens (incl. Microsoft access/refresh tokens) | `profiles.json` | **High — plain text** |
| Profiles, settings, servers list | `config.json` | Low-medium |
| AI API key (if you use AI themes) | `cerebras_api_key.txt` | **High — plain text** |
| Generated themes | `custom_themes.json`, `custom_themes_web.json` | Low |
| Cached skins | `skins/*.png` | Low |
| World backups (zip) | `backups/*.zip` | User content |
| Uploaded fonts | `fonts/` | User content |
| Diagnostic log | `launcher.log` | Low |

9.3 **What is sent to third parties** (and only when you use the corresponding feature):

- authentication/refresh requests → Microsoft, Xbox, Minecraft Services;
- profile/skin lookups → Mojang session servers;
- search/download requests → Modrinth; mod metadata → loader repositories;
- theme prompts + your API key → Cerebras (AI themes only);
- one status packet → the game server whose IP you ping.

9.4 **Your responsibilities:** secure your device, do not share the `~/.FractalLauncher/` folder, and
understand that **plain-text token storage is a deliberate simplicity trade-off with real risk**. If your
machine is compromised, your Microsoft tokens may be exposed — revoke sessions via your Microsoft account
security page if you suspect compromise.

9.5 **Deletion:** uninstalling the Software and deleting `~/.FractalLauncher/` erases all local data.
FractalLabs retains nothing because nothing is sent to us.

9.6 **Backups you export** (world zips, screenshots) are your data; handle them as you see fit.

## 10. User Content

10.1 **"User Content"** means anything you supply through the Software: usernames, skins, capes, server
entries, screenshots, notes (JVM notepad), themes you write, and backup content.

10.2 You warrant that you own or have all necessary rights to your User Content, and that its use as
contemplated by the Software does not infringe any third-party rights.

10.3 You must not use User Content for anything illegal, hateful, exploitative, or infringing. FractalLabs
has no ability to moderate content that never leaves your device — but you remain responsible for how you
use and share it (e.g., a skin you distribute on a server).

10.4 Since User Content generally never leaves your device, FractalLabs neither reviews nor stores it.

## 11. Disclaimers

11.1 **THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR
IMPLIED**, as detailed in EULA §9, including implied warranties of merchantability, fitness for a particular
purpose, and non-infringement.

11.2 Without limiting the above, FractalLabs does **not** warrant that:

- the Software will work with every Minecraft version, mod, mod loader, server or hardware configuration;
- Microsoft/Mojang/Modrinth/Cerebras integrations will remain functional (they may change or break without
  any action by us);
- the Software is free of defects, or that downloads (game files, mods, installers) are complete or
  error-free — while official downloads are checksum-verified where available, FractalLabs is not a guarantor
  of third-party downloads;
- offline mode, AI themes, server pings or backups will meet your expectations.

11.3 FractalLabs does not provide technical support unless and where it chooses to do so voluntarily.

## 12. Limitation of Liability

12.1 To the maximum extent permitted by applicable law, FractalLabs and its contributors shall not be liable
for any indirect, incidental, special, consequential or punitive damages, or any loss of data, accounts,
worlds, saves, tokens, profits or goodwill, arising from your use of (or inability to use) the Software —
including but not limited to account bans, token theft, corrupted worlds, failed backups, outages of
third-party services, or AI-generated content, as further specified in EULA §10.

12.2 Our total aggregate liability shall not exceed the greater of the amount you paid us in the twelve
months before the claim (**€0** for the free Software) or **€10.00**.

12.3 Some jurisdictions do not allow certain limitations; in those cases, our liability is limited to the
fullest extent permitted by law.

## 13. Termination and Uninstall

13.1 **You may stop using the Software at any time** by uninstalling it; no notice to FractalLabs is
required.

13.2 **We may restrict or terminate** your license by publishing a notice or by making the Software
unavailable, if you breach these Terms (EULA §8). Since we have no server-side control over your local
installation, "termination" means your right to use the Software ends; you must then uninstall it.

13.3 **Effect of termination:** stop all use, uninstall, and destroy copies. Sections that by their nature
should survive (disclaimers, liability limits, indemnity, governing law) survive termination.

13.4 **No data retention by us:** termination has no effect on third-party services; if you need to revoke
access granted through the Software, revoke it at the provider (e.g., Microsoft account security → apps with
account access; Cerebras dashboard → API keys).

## 14. Changes to These Terms

14.1 FractalLabs may update these Terms at any time. The current version is always the copy distributed with
the Software, with its effective date at the top.

14.2 Material changes will be indicated by bumping the version number/date; where practical, a notice will
also appear in the Software or the project documentation.

14.3 Your continued use of the Software after updated Terms are published constitutes acceptance of them. If
you do not agree, uninstall the Software.

## 15. Precedence of Third-Party Terms

For any subject matter governed by a third party's terms (Microsoft/Xbox authentication, Mojang/Minecraft
services, Modrinth content, Cerebras AI, loader repositories, individual Mods), **that third party's terms
prevail**. These Terms and the EULA govern the relationship between you and FractalLabs only.

## 16. Miscellaneous

1. **Severability.** If any provision is unenforceable, it shall be modified to the minimum extent necessary
   and the remainder stays in effect.
2. **No class actions / waiver of jury trial** — to the extent permitted by applicable law, claims must be
   brought individually, not as part of a class or representative action.
3. **Entire agreement.** These Terms plus the EULA (and the MIT License for the Source Code) are the entire
   agreement between you and FractalLabs.
4. **No waiver.** Failure to enforce a provision is not a waiver.
5. **Assignment.** You may not transfer these Terms; FractalLabs may assign them in connection with a
   project transfer or reorganization.
6. **Force majeure.** We are not liable for failures caused by events beyond reasonable control (third-party
   outages, internet failures, acts of God).
7. **Headings** are for convenience only.

## 17. Contact

Questions about these Terms:

- **FractalLabs** — email: **contact@FractalLauncher.dev**

---

*© 2026 FractalLabs. FractalLauncher is an unofficial tool, not affiliated with Mojang Studios or
Microsoft Corporation. Minecraft, Mojang and Xbox are trademarks of their respective owners.*
