import { FeatureHighlights } from "@/components/landing/feature-highlights";
import { HeroSection } from "@/components/landing/hero-section";
import { HowItWorks } from "@/components/landing/how-it-works";
import { SiteFooter } from "@/components/landing/site-footer";

export default function HomePage() {
  return (
    <main className="relative overflow-hidden">
      <HeroSection />
      <FeatureHighlights />
      <HowItWorks />
      <SiteFooter />
    </main>
  );
}
