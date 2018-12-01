#!/bin/bash
for i in 1 2 3; do
          git push ksun --tags && break
          echo "Couldn't push tags--please try again"
done
