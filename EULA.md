# End User License Agreement (EULA)

**FractalLauncher** — published by **FractalLabs**

*Effective date: October 22, 2026 · Version 1.0 · Contact: contact@FractalLauncher.dev*

---

**IMPORTANT — READ CAREFULLY.** This End User License Agreement ("EULA") is a legal agreement between you
("you", "the user", "Licensee") and FractalLabs ("FractalLabs", "we", "us", "our") for the software product
**FractalLauncher v1.2.4 (Optimize Patch)** and later versions, including the executable, all associated files, and every
third-party component bundled with it (collectively, the "Software").

By downloading, installing, copying, running, or otherwise using the Software, you acknowledge that you have
read, understood, and agree to be bound by the terms of this EULA. **If you do NOT agree to these terms, do not
use the Software — delete it and all of its components from your devices.**

If a separate Terms of Service ("TOS") accompanies the Software, both documents apply: this EULA governs your
license to the Software itself, and the TOS governs your use of the Software's features and the third-party
services it interacts with. In the event of a conflict regarding licensing of the Software, this EULA controls;
regarding use of features and services, the TOS controls.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **"Software"** | The FractalLauncher application in any form (source code, compiled executable, installers, archives), together with all files, assets, documentation, configuration presets, bundled runtimes and libraries distributed with it. |
| **"Bundled Components"** | Third-party software included within or distributed alongside the Software — including but not limited to the Oracle JDK, runtime Python libraries, JavaScript libraries, and the authlib-injector JAR (see Section 4). |
| **"Object Code" / "Executable"** | The compiled, non-source form of the Software (e.g., `FractalLauncher.exe`). |
| **"You" / "Licensee"** | The individual or legal entity obtaining a license under this EULA. |
| **"Third-Party Services"** | External services reached through the Software, such as Microsoft/Xbox, Mojang/Minecraft, Modrinth, Cerebras, and mod-loader repositories. |
| **"Source Code"** | The human-readable Python, HTML, CSS and JavaScript source files of the FractalLauncher launcher itself, as distributed in this repository. |

## 2. License Grant

Subject to your complete and continuous compliance with this EULA, FractalLabs grants you a personal,
limited, non-exclusive, non-transferable, non-sublicensable, revocable license to:

- **(a)** install and run the Object Code of the Software on devices you own or control, for personal,
      non-commercial use;
- **(b)** use the Software's features (launching Minecraft, managing profiles/accounts/mods, and related
      functionality) in accordance with this EULA and the accompanying TOS;
- **(c)** make reasonable private backup copies of the Software for archival purposes.

### 2.1 Relationship to the MIT License (Source Code)

The **launcher's own Source Code** in this repository is separately released under the **MIT License** (see
`README.md`). Nothing in this EULA limits your rights under the MIT License with respect to *that Source Code
in isolation*.

This EULA governs the **assembled Software as a product** — in particular the compiled Executable and the
Bundled Components, which include third-party material that is **not** MIT-licensed (most notably the Oracle
JDK, covered in Section 4). Where this EULA and the MIT License cover the same material, **this EULA applies
to the assembled distribution** because it carries the obligations imposed by the licenses of the components
we did not author.

### 2.2 Scope note

This license is **per-user, not per-device**. It applies to your personal use across your own devices. It does
not grant you any ownership interest in the Software.

## 3. Restrictions

Except as expressly permitted by this EULA, the MIT License (for Source Code), or by mandatory applicable law,
you must **not**:

1. **Redistribute or resell** the Software, the Executable, or the assembled bundle (including the Software
   bundled with the Oracle JDK or other Bundled Components) as a product, service, or paid offering, or pass
   it off as your own.
2. **Sell, rent, lease, sublicense or trade** the Software or any rights granted under it.
3. **Modify the Executable** to remove, obscure, or alter copyright, trademark, license or attribution
   notices — including notices embedded in Bundled Components — except where the applicable open-source
   license expressly permits it.
4. **Reverse engineer, decompile, or disassemble** the Object Code of the Software or any Bundled Component,
   to the extent such restriction is not prohibited by mandatory applicable law. (Your rights to inspect the
   launcher's own Source Code are governed by the MIT License and are not restricted by this clause.)
5. **Circumvent or bypass** authentication, entitlement, or security mechanisms reached through the Software,
   or use the Software to gain access to accounts, content, or services you are not authorized to access.
6. **Use the Software for illegal purposes**, for the distribution of malware, or to violate the terms of any
   Third-Party Service (see Section 5 and the TOS).
7. **Remove, disable or obscure** licensing, telemetry-free-operation disclosures, or technical protection
   features of any Bundled Component.
8. **Export or use the Software** in violation of applicable export-control, sanctions, or other laws.

## 4. Third-Party Components (Bundled Components)

The Software incorporates or bundles third-party open-source and proprietary components, each under its own
license. **Your use of each component is governed by its own license, which prevails over this EULA for that
component.** The principal components are:

| Component | License / Terms | Notes |
|---|---|---|
| **Oracle JDK 25.0.2** (bundled in `jdk/`) | Oracle **No-Fee Terms and Conditions (NFTC)** — <https://www.oracle.com/downloads/licenses/no-fee-license.html> | ⚠ **Not covered by MIT.** Redistribution of the Oracle JDK is subject to Oracle's NFTC terms. If you redistribute the Software, you must comply with the Oracle JDK license separately, or remove `jdk/`. |
| **minecraft-launcher-lib** | MIT | Python library; downloads/install logic |
| **pywebview** | MIT | Window/bridge framework |
| **Pillow (PIL)** | MIT-CMU (HPND) | Image processing |
| **requests** | Apache-2.0 | HTTP |
| **cryptography** | Apache-2.0 OR BSD-3-Clause | Used for RSA texture signing |
| **CustomTkinter** | MIT | Legacy UI fallback dependency |
| **skinview3d v3.4.2** (`assets/lib/skinview3d.bundle.js`) | MIT | 3D skin viewer |
| **three.js r156** (embedded in skinview3d bundle) | MIT | WebGL engine |
| **Authlib-Injector** (`Authlib/Authlib.jar`) | Original upstream license (Mojang-ecosystem open-source tool) | Java agent for skin/auth injection |
| **Microsoft Edge WebView2 Runtime** | Microsoft Edge / WebView2 license | Provided by Windows/the OS, not by us |
| **ModLoader installers** (Fabric / Quilt / Forge / NeoForge) | Their respective licenses | Downloaded from official Maven repositories at your request |
| **Configuration presets** (`config/`) | Community mod configs (Sodium, Lithium, ModernFix, EntityCulling, etc.) | Each belongs to its mod's authors |

Full license texts for OS-bundled components are shipped where required, e.g. under `jdk/legal/`.

**Disclaimer:** FractalLabs is not the author of these components and provides them without any warranty of
any kind (see Section 9). The inclusion of a component does not imply endorsement by its authors.

## 5. Microsoft, Xbox and Mojang/Minecraft Disclaimer

- FractalLabs is **not affiliated with, endorsed by, sponsored by, or connected to** Mojang Studios,
  Microsoft Corporation, Xbox, or any of their affiliates.
- **Minecraft**, **Mojang**, **Xbox** and related trademarks, names and assets are the property of their
  respective owners. The Software is an independent, unofficial tool.
- Microsoft login in the Software uses a publicly available OAuth client registration; authentication traffic
  goes directly between your device and Microsoft's servers. **FractalLabs never receives, stores on its own
  servers, or has any access to your Microsoft password.** (Access/refresh tokens are stored only locally on
  your device — see TOS §9.)
- Your use of Microsoft, Xbox, Mojang and Minecraft services is governed exclusively by **their** terms and
  privacy policies. It is your responsibility to review and comply with them, including the Minecraft End User
  License Agreement and the Xbox/Microsoft Services Agreement.
- The **offline-mode** functionality of the Software is unofficial and not provided by Mojang or Microsoft;
  its availability and permissibility are your sole responsibility (see TOS §4).

## 6. Open-Source Compliance and Attribution

Where the Software's own Source Code (MIT License) is distributed, the copyright notice and permission notice
of the MIT License must be preserved. Where Bundled Components are redistributed, their license headers,
notices and license texts must remain intact and be made available to recipients. Nothing in this EULA
prevents you from exercising rights expressly granted by any applicable open-source license.

## 7. Updates, New Versions and Feature Changes

- FractalLabs may release updates, patches, new versions or removals of features at any time, with or without
  notice.
- This EULA applies to every update or new version of the Software unless a replacement agreement accompanies
  it, in which case that agreement governs the updated Software.
- Updates may change third-party integrations (e.g., OAuth clients, API endpoints, mod sources) as services
  evolve.

## 8. Termination

This license is effective until terminated.

- **Automatic termination:** your license terminates automatically, without notice, if you breach any term of
  this EULA.
- **Effect of termination:** you must immediately stop using the Software and destroy all copies (including
  the Executable and Bundled Components) in your possession. Sections 1, 4, 9, 10, 11, 12 and 13 survive
  termination.
- **Your right to stop at any time:** you may terminate this EULA at any time by permanently uninstalling the
  Software and deleting all copies, without prejudice to any rights of FractalLabs that arose prior to
  termination.
- **No refund:** the Software is provided free of charge; no refund of any kind is due, to the extent refunds
  are even applicable.

## 9. Disclaimer of Warranties

**TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE",
WITHOUT WARRANTY OF ANY KIND, WHETHER EXPRESS, IMPLIED, STATUTORY OR OTHERWISE.**

FRACTALLABS EXPRESSLY DISCLAIMS ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO:

- **(a)** IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT;
- **(b)** ANY WARRANTY THAT THE SOFTWARE WILL BE UNINTERRUPTED, TIMELY, SECURE OR ERROR-FREE, OR THAT DEFECTS
      WILL BE CORRECTED;
- **(c)** ANY WARRANTY REGARDING ACCURACY, RELIABILITY OR THE RESULTS OBTAINED THROUGH THE SOFTWARE;
- **(d)** ANY WARRANTY ARISING FROM COURSE OF DEALING OR USAGE OF TRADE;
- **(e)** ANY WARRANTY CONCERNING THIRD-PARTY SERVICES, THIRD-PARTY CONTENT, MODS, SERVERS, OR BUNDLED
      COMPONENTS, ALL OF WHICH ARE PROVIDED BY THEIR OWN AUTHORS UNDER THEIR OWN TERMS.

YOU EXPRESSLY ASSUME ALL RISK AND RESPONSIBILITY FOR THE USE OF THE SOFTWARE. IN PARTICULAR, NO ADVICE OR
INFORMATION (ORAL OR WRITTEN) OBTAINED FROM FRACTALLABS OR THROUGH THE SOFTWARE SHALL CREATE ANY WARRANTY NOT
EXPRESSLY STATED HEREIN.

## 10. Limitation of Liability

**TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL FRACTALLABS, ITS CONTRIBUTORS,
MAINTAINERS, CONTRIBUTORS, OR AFFILIATES BE LIABLE FOR ANY:**

- **(a)** INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY OR PUNITIVE DAMAGES;
- **(b)** LOSS OF PROFITS, DATA, GOODWILL, BUSINESS OPPORTUNITY, OR COMPUTER DAMAGE (INCLUDING CORRUPTION);
- **(c)** DAMAGE RESULTING FROM INTERRUPTED OR LOST GAME SESSIONS, CORRUPTED WORLDS OR SAVES, LOST MODS,
      LOST SCREENSHOTS, LOST BACKUPS, OR LOST ACCOUNT ACCESS;
- **(d)** DAMAGE RESULTING FROM THIRD-PARTY SERVICE OUTAGES, API CHANGES, BANS OR RESTRICTIONS IMPOSED BY
      MICROSOFT, MOJANG, MODRINTH, CEREBRAS OR ANY OTHER THIRD PARTY;
- **(e)** DAMAGE RESULTING FROM THE STORAGE, LOSS, THEFT OR COMPROMISE OF LOCALLY STORED ACCOUNT TOKENS;

**WHETHER BASED IN CONTRACT, TORT (INCLUDING NEGLIGENCE), STRICT LIABILITY OR ANY OTHER THEORY, EVEN IF
FRACTALLABS HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.**

IN ALL CASES, FRACTALLABS' TOTAL AGGREGATE LIABILITY UNDER OR IN CONNECTION WITH THIS EULA SHALL NOT EXCEED
THE GREATER OF (I) THE AMOUNT YOU PAID FRACTALLABS FOR THE SOFTWARE IN THE TWELVE (12) MONTHS PRECEDING THE
CLAIM (WHICH IS **ZERO** FOR THE FREE SOFTWARE) OR (II) **€10.00 (TEN EUROS)**.

Some jurisdictions do not allow the exclusion or limitation of certain damages; in such cases, our liability is
limited to the fullest extent permitted by law.

## 11. Indemnification

You agree to defend, indemnify and hold harmless FractalLabs and its contributors, maintainers and affiliates
from and against any and all claims, damages, obligations, losses, liabilities, costs and expenses (including
reasonable attorneys' fees) arising from: **(a)** your use of the Software; **(b)** your violation of any term
of this EULA or the TOS; **(c)** your violation of any third-party right, including any intellectual property
or privacy right; or **(d)** your use of Third-Party Services reached through the Software.

## 12. Governing Law and Disputes

This EULA shall be governed by and construed in accordance with the laws applicable in your jurisdiction of
residence, without regard to conflict-of-law principles, **to the extent permitted by applicable law**. Any
disputes arising out of or relating to this EULA shall be resolved in the competent courts of your place of
residence, to the extent permitted by mandatory applicable law. If any provision of this EULA is held
unenforceable, the remaining provisions remain in full force.

## 13. Miscellaneous

1. **Severability.** If any provision is held invalid or unenforceable, it shall be modified to the minimum
   extent necessary to make it enforceable, and the remainder of this EULA shall continue in effect.
2. **No waiver.** Failure to enforce any provision is not a waiver of the right to do so later.
3. **Entire agreement.** This EULA, together with the TOS and the MIT License (for Source Code), constitutes
   the entire agreement between you and FractalLabs concerning the Software and supersedes all prior or
   contemporaneous communications.
4. **Assignment.** You may not assign or transfer this EULA or any rights under it. FractalLabs may assign
   this agreement as part of a reorganization, merger, or transfer of the project.
5. **Force majeure.** FractalLabs is not liable for failures caused by events beyond its reasonable control
   (including outages of Microsoft, Mojang, Modrinth, Cerebras, hosting providers, or the internet).
6. **Headings.** Section headings are for convenience only and do not affect interpretation.

## 14. Contact

Questions about this EULA:

- **FractalLabs** — email: **contact@FractalLauncher.dev**

---

*© 2026 FractalLabs. FractalLauncher is distributed under this EULA; the launcher's own source code is
additionally available under the MIT License. All third-party trademarks are the property of their owners.*
