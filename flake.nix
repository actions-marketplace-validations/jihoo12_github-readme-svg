{
  description = "Animated SVG banner generator for GitHub README";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f nixpkgs.legacyPackages.${s});
    in {
      packages = forAll (pkgs: {
        default = pkgs.writeShellApplication {
          name = "readme-svg";
          runtimeInputs = [ pkgs.python3 ];
          text = ''exec python3 ${./generate.py} "$@"'';
        };
      });

      apps = forAll (pkgs: {
        default = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/readme-svg";
        };
      });

      devShells = forAll (pkgs: {
        # librsvg: rsvg-convert로 PNG 미리보기 확인용
        default = pkgs.mkShell { packages = [ pkgs.python3 pkgs.librsvg ]; };
      });
    };
}
