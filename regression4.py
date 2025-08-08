try:
    import matplotlib.pyplot as plt
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

try:
    import pandas as pd
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import gaussian_kde
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn scipy"])
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import gaussian_kde

import numpy as np

# ================================================
# Stability & Fertility Parameter Sweep — Real Data Run
# ================================================

# ------------------------------------------------
# 1. Baseline constants (from real data sources)
# ------------------------------------------------
# CODATA 2018, Planck 2018, PDG 2020
alpha_0 = 1 / 137.035999084    # Fine-structure constant
G_0 = 6.67430e-11             # Gravitational constant (m^3 kg^-1 s^-2)
mu_0 = 1836.15267389          # Proton-to-electron mass ratio
alpha_s_0 = 0.1181             # Strong coupling constant (approximate from lattice QCD)
lambda_0 = 1.1056e-52         # Cosmological constant (m^-2, Planck 2018)
G_F_0 = 1.1663787e-5          # Fermi coupling constant (GeV^-2)
h_0 = 6.62607015e-34          # Planck constant (J·s)
k_B_0 = 1.380649e-23          # Boltzmann constant (J/K)
c_0 = 299792458               # Speed of light (m/s)
e_0 = 1.602176634e-19         # Electron charge (C)
h_bar_0 = h_0 / (2 * np.pi)   # Reduced Planck constant (J·s)
m_e_0 = 9.10938356e-31        # Electron mass (kg)
mu_0_mag = 4 * np.pi * 1e-7   # Magnetic constant (H/m)

# Uncertainties from CODATA 2018 and Planck 2018 (relative standard uncertainties)
alpha_unc = 2.1e-10 * alpha_0  # ~0.021 ppm
G_unc = 1.5e-5 * G_0           # ~1.5%
mu_unc = 7.9e-11 * mu_0        # ~0.079 ppm
alpha_s_unc = 0.001 * alpha_s_0  # ~0.1% (approximate)
lambda_unc = 0.1 * lambda_0    # ~10% (large uncertainty from Planck)
G_F_unc = 6e-7 * G_F_0         # ~0.06 ppm
h_unc = 1e-8 * h_0             # ~0.01 ppm
k_B_unc = 1e-6 * k_B_0         # ~0.1 ppm
c_unc = 0.0 * c_0              # Exact by definition
e_unc = 1.3e-8 * e_0           # ~0.013 ppm
h_bar_unc = h_unc / (2 * np.pi)
m_e_unc = 2.2e-11 * m_e_0      # ~0.022 ppm
mu_0_mag_unc = 0.0 * mu_0_mag  # Exact by definition

# ------------------------------------------------
# 3. Evaluation functions with real-data proxies (moved to be defined before use)
# ------------------------------------------------
def hydrogen_binding_energy(alpha, e, m_e):
    return -13.6 * (alpha / alpha_0)**2 * (e / e_0)**2 / (m_e / m_e_0)

def nuclear_force_strength(alpha_s, h_bar):
    return alpha_s * (h_bar_0 / h_bar)

def gravity_strength(G):
    return G

def check_stellar_fusion(alpha, alpha_s, h, m_e):
    # Proxy using carbon production (Hoyle state resonance)
    coulomb_barrier = alpha / alpha_0 * (m_e_0 / m_e)
    fusion_rate = alpha_s / alpha_s_0 * (h_0 / h)
    ratio = fusion_rate / coulomb_barrier
    return max(0.0, min(1.0, 1 - abs(ratio - 1.0) / 0.5)) * (1.0 if abs(alpha - alpha_0) < 2*alpha_unc else 0.9)

def check_multi_element(alpha, mu, e, m_e):
    second_shell_energy = -13.6 / 4 * (alpha / alpha_0)**2 * (e / e_0)**2 / (m_e / m_e_0)
    # Based on observed element stability (e.g., carbon, oxygen)
    if second_shell_energy >= -0.1 or abs(mu - mu_0) > 10 * mu_unc:
        return 0.0
    return min(1.0, max(0.0, 1 - abs(mu - mu_0) / (10 * mu_unc)))

def check_heavy_element_synthesis(alpha_s, h, h_bar):
    # Based on observed heavy element abundance (e.g., iron peak)
    binding_energy = 8.0 * (alpha_s / alpha_s_0) * (h_0 / h) * (h_bar_0 / h_bar)
    return max(0.0, min(1.0, 1 - abs(binding_energy - 8.0) / 2.0)) * (1.0 if abs(alpha_s - alpha_s_0) < 2*alpha_s_unc else 0.9)

def check_cosmo_structure(lambda_val, G, c, mu_0_mag):
    # Based on CMB and large-scale structure (Planck data)
    # Corrected usage of mu_0_mag: ensure mu_0_mag_0 is defined if used.
    # Assuming mu_0_mag_0 should be mu_0_mag as it's a constant
    structure_factor = (lambda_val / lambda_0) * (G_0 / G) * (mu_0_mag / mu_0_mag) # mu_0_mag_0 corrected to mu_0_mag
    return max(0.0, min(1.0, 1 - abs(structure_factor - 1.0) / 0.2)) * (1.0 if abs(lambda_val - lambda_0) < 2*lambda_unc else 0.9)

def check_nucleosynthesis(G_F, k_B, m_e):
    # Based on observed light element abundances (Big Bang nucleosynthesis)
    weak_strength = G_F / G_F_0 * (k_B_0 / k_B) * (m_e_0 / m_e)
    return max(0.0, min(1.0, 1 - abs(weak_strength - 1.0) / 0.1)) * (1.0 if abs(G_F - G_F_0) < 2*G_F_unc else 0.9)

def calculate_fertility_score(alpha, G, mu, alpha_s, lambda_val, G_F, h, k_B, c, e, h_bar, m_e, mu_0_mag):
    score = (
        (1.0 if hydrogen_binding_energy(alpha, e, m_e) < 0 else 0.0) +
        check_stellar_fusion(alpha, alpha_s, h, m_e) +
        check_multi_element(alpha, mu, e, m_e) +
        check_heavy_element_synthesis(alpha_s, h, h_bar) +
        check_cosmo_structure(lambda_val, G, c, mu_0_mag) +
        check_nucleosynthesis(G_F, k_B, m_e)
    ) / 6.0
    return score

def check_stability(alpha, G, mu, alpha_s, lambda_val, G_F, h, c, e, h_bar, m_e, mu_0_mag):
    if not hydrogen_binding_energy(alpha, e, m_e) < 0:
        return False
    if not nuclear_force_strength(alpha_s, h_bar) > 0.05:
        return False
    if not (0.99 * G_0 < G < 1.01 * G_0):  # Tight constraint from observations
        return False
    if not (c_0 * 0.9999 < c < c_0 * 1.0001):  # Near-exact
        return False
    return True


# ------------------------------------------------
# 2. Generate real-data-based parameter sweep
# ------------------------------------------------
N = 10000
np.random.seed(42)

samples = []
for _ in range(N):
    alpha = np.random.normal(alpha_0, alpha_unc)
    G = np.random.normal(G_0, G_unc)
    mu = np.random.normal(mu_0, mu_unc)
    alpha_s = np.random.normal(alpha_s_0, alpha_s_unc)
    lambda_val = np.random.normal(lambda_0, lambda_unc)
    G_F = np.random.normal(G_F_0, G_F_unc)
    h = np.random.normal(h_0, h_unc)
    k_B = np.random.normal(k_B_0, k_B_unc)
    c = c_0  # Fixed due to exactness
    e = np.random.normal(e_0, e_unc)
    h_bar = np.random.normal(h_bar_0, h_bar_unc)
    m_e = np.random.normal(m_e_0, m_e_unc)
    mu_0_mag = mu_0_mag  # Fixed due to exactness

    # Anthropic constraints (approximate bounds from literature)
    if not (0.007 < alpha < 0.008 and 1800 < mu < 1900 and 1e-11 < G < 1e-10):
        continue  # Skip samples outside plausible anthropic limits

    stable = check_stability(alpha, G, mu, alpha_s, lambda_val, G_F, h, c, e, h_bar, m_e, mu_0_mag)
    fertility = calculate_fertility_score(alpha, G, mu, alpha_s, lambda_val, G_F, h, k_B, c, e, h_bar, m_e, mu_0_mag)
    samples.append({
        'alpha': alpha,
        'G': G,
        'mu': mu,
        'alpha_s': alpha_s,
        'lambda': lambda_val,
        'G_F': G_F,
        'h': h,
        'k_B': k_B,
        'c': c,
        'e': e,
        'h_bar': h_bar,
        'm_e': m_e,
        'mu_0_mag': mu_0_mag,
        'stable': stable,
        'fertility': fertility
    })

df = pd.DataFrame(samples)
df.to_csv('constants_sweep_real.csv', index=False)
print(f'Saved {len(df)} samples to "constants_sweep_real.csv"')

# ------------------------------------------------
# 5. Stability Contour
# ------------------------------------------------
plt.figure(figsize=(10, 6))
stable_df = df[df['stable']].copy()
kde = gaussian_kde(np.vstack([stable_df['alpha'], stable_df['mu']]))
alpha_vals = np.linspace(min(df['alpha']), max(df['alpha']), 50)
mu_vals = np.linspace(min(df['mu']), max(df['mu']), 50)
AA, MM = np.meshgrid(alpha_vals, mu_vals)
positions = np.vstack([AA.ravel(), MM.ravel()])
stability_probs = kde(positions).reshape(AA.shape)
plt.contourf(AA, MM, stability_probs, levels=20, cmap='Blues')
plt.scatter(alpha_0, mu_0, color='red', s=100, marker='*', label='Our Universe')  # Changed to red
max_stab_idx = np.unravel_index(np.argmax(stability_probs), stability_probs.shape)
stab_sweet_alpha = AA[max_stab_idx]
stab_sweet_mu = MM[max_stab_idx]
plt.scatter(stab_sweet_alpha, stab_sweet_mu, color='blue', s=100, marker='x', label='Stability Sweet Spot')
plt.xlabel('Fine-Structure Constant (alpha)')
plt.ylabel('Proton-Electron Mass Ratio (mu)')
plt.title('Stability Probability Contours')
plt.colorbar(label='Stability Probability')
plt.legend()
plt.show()

# ------------------------------------------------
# 6. Fertility Contour
# ------------------------------------------------
features = df[['alpha', 'G', 'mu', 'alpha_s', 'lambda', 'G_F', 'h', 'k_B', 'c', 'e', 'h_bar', 'm_e', 'mu_0_mag']].values
labels = df['fertility'].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)
model = LinearRegression()
model.fit(X_scaled, labels)

G_mean = df['G'].mean()
alpha_s_mean = df['alpha_s'].mean()
lambda_mean = df['lambda'].mean()
G_F_mean = df['G_F'].mean()
h_mean = df['h'].mean()
k_B_mean = df['k_B'].mean()
c_mean = df['c'].mean()
e_mean = df['e'].mean()
h_bar_mean = df['h_bar'].mean()
m_e_mean = df['m_e'].mean()
mu_0_mag_mean = df['mu_0_mag'].mean()

alpha_vals = np.linspace(min(df['alpha']), max(df['alpha']), 50)
mu_vals = np.linspace(min(df['mu']), max(df['mu']), 50)
AA, MM = np.meshgrid(alpha_vals, mu_vals)
fertility_probs = np.zeros_like(AA)

for i in range(AA.shape[0]):
    for j in range(AA.shape[1]):
        X_point = np.array([[AA[i, j], G_mean, MM[i, j], alpha_s_mean, lambda_mean, G_F_mean, h_mean, k_B_mean, c_mean, e_mean, h_bar_mean, m_e_mean, mu_0_mag_mean]])
        X_scaled = scaler.transform(X_point)
        fertility_probs[i, j] = model.predict(X_scaled)[0]

plt.figure(figsize=(10, 6))
contour = plt.contourf(AA, MM, fertility_probs, levels=20, cmap='Greens')
plt.colorbar(contour, label='Fertility Score (0-1)')
plt.scatter(alpha_0, mu_0, color='red', s=100, marker='*', label='Our Universe')  # Changed to red
max_fert_idx = np.unravel_index(np.argmax(fertility_probs), fertility_probs.shape)
fert_sweet_alpha = AA[max_fert_idx]
fert_sweet_mu = MM[max_fert_idx]
plt.scatter(fert_sweet_alpha, fert_sweet_mu, color='green', s=100, marker='x', label='Fertility Sweet Spot')
plt.xlabel('Fine-Structure Constant (alpha)')
plt.ylabel('Proton-Electron Mass Ratio (mu)')
plt.title('Fertility Probability Contours')
plt.legend()
plt.show()

# ------------------------------------------------
# 7. Combined Sweet Spot Regression
# ------------------------------------------------
stability_norm = stability_probs / np.max(stability_probs)
combined_score = (stability_norm + fertility_probs) / 2

plt.figure(figsize=(10, 6))
contour = plt.contourf(AA, MM, combined_score, levels=20, cmap='RdYlBu')
plt.colorbar(contour, label='Combined Score (0-1)')
plt.scatter(alpha_0, mu_0, color='red', s=100, marker='*', label='Our Universe')  # Changed to red
max_combined_idx = np.unravel_index(np.argmax(combined_score), combined_score.shape)
combined_sweet_alpha = AA[max_combined_idx]
combined_sweet_mu = MM[max_combined_idx]
plt.scatter(combined_sweet_alpha, combined_sweet_mu, color='red', s=100, marker='x', label='Combined Sweet Spot')
plt.xlabel('Fine-Structure Constant (alpha)')
plt.ylabel('Proton-Electron Mass Ratio (mu)')
plt.title('Combined Stability-Fertility Sweet Spot')
plt.legend()
plt.show()

print(f"Stable samples: {df['stable'].sum()} / {N}")
print(f"Average fertility score: {df['fertility'].mean():.3f}")
print(f"Stability Sweet Spot (alpha, mu): ({stab_sweet_alpha:.6f}, {stab_sweet_mu:.6f})")
print(f"Fertility Sweet Spot (alpha, mu): ({fert_sweet_alpha:.6f}, {fert_sweet_mu:.6f})")
print(f"Combined Sweet Spot (alpha, mu): ({combined_sweet_alpha:.6f}, {combined_sweet_mu:.6f})")
