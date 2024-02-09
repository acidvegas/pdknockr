#!/usr/bin/env python
# Passive DNS Knocker (PDK) - developed by acidvegas in python (https://git.acid.vegas/pdknockr)

import asyncio
import json
import logging
import logging.handlers
import random
import time

try:
    import aiodns
except ImportError:
    raise SystemExit('missing required \'aiodns\' module (pip install aiodns)')


async def dns_lookup(domain: str, subdomain: str, dns_server: str, dns_type: str, timeout: int, semaphore: asyncio.Semaphore):
    '''
    Perform a DNS lookup on a target domain.
    
    :param domain: The target domain to perform the lookup on.
    :param subdomain: The subdomain to look up.
    :param dns_server: The DNS server to perform the lookup on.
    :param dns_type: The DNS record type to look up.
    :param timeout: The timeout for the DNS lookup.
    :param semaphore: The semaphore to use for concurrency.
    '''
    async with semaphore:
        target = f'{subdomain}.{domain}'
        resolver = aiodns.DNSResolver(nameservers=[dns_server], timeout=timeout)
        logging.info(f'\033[96mKnocking {target}\033[0m on \033[93m{dns_server}\033[0m (\033[90m{dns_type}\033[0m)')
        try:
            await resolver.query(target, dns_type)
        except Exception as e:
            pass


def generate_subdomain(sub_domains: list) -> str:
    '''
    Generate a random subdomain.

    :param sub_domains: The list of subdomains to use.
    '''
    chosen_domains = random.sample(sub_domains, 2)
    if random.choice([True, False]):
        chosen_index = random.choice([0, 1])
        chosen_domains[chosen_index] =  chosen_domains[chosen_index] + str(random.randint(1, 99))
    return random.choice(['.', '-']).join(chosen_domains)

    
async def main(args):
    '''
    Main function for the program.
    
    :param args: The arguments passed to the program.
    '''
    global dns_keys

    semaphore = asyncio.BoundedSemaphore(args.concurrency)
    tasks = []

    while True:
        for domain in args.domains.split(','):
            for dns_server in dns_keys:
                if len(tasks) < args.concurrency:
                    query_record = random.choice(args.rectype)
                    task = asyncio.create_task(dns_lookup(domain, dns_keys[dns_server], dns_server, query_record, args.timeout, semaphore))
                    tasks.append(task)
                else:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
        if not args.noise:
            break



if __name__ == '__main__':
    import argparse
    import os
    import urllib.request

    parser = argparse.ArgumentParser(description='Passive DNS Knocking Tool')
    parser.add_argument('-d', '--domains', help='Comma seperate list of domains or file containing list of domains')
    #parser.add_argument('-s', '--subdomain', help='Subdomain to look up')
    parser.add_argument('-c', '--concurrency', type=int, default=50, help='Concurrency limit (default: 50)')
    parser.add_argument('-r', '--resolvers', help='File containing list of DNS resolvers (uses public-dns.info if not specified)')
    parser.add_argument('-rt', '--rectype', default='A,AAAA', help='Comma-seperated list of  DNS record type (default: A)')
    parser.add_argument('-t', '--timeout', type=int, default=3, help='Timeout for DNS lookup (default: 3)')
    parser.add_argument('-n', '--noise', action='store_true', help='Enable random subdomain noise')
    args = parser.parse_args()

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(message)s', '%I:%M %p'))
    os.makedirs('logs', exist_ok=True)
    log_filename = time.strftime('pdk_%Y-%m-%d_%H-%M-%S.log')
    fh = logging.handlers.RotatingFileHandler(f'logs/{log_filename}.log', maxBytes=2500000, backupCount=3, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(filename)s.%(funcName)s.%(lineno)d | %(message)s', '%Y-%m-%d %I:%M %p')) 
    logging.basicConfig(level=logging.NOTSET, handlers=(sh,fh))

    if not args.domains:
        raise SystemExit('no domains specified')
    
    if args.rectype:
        valid_record_types = ('A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT')
        if ',' in args.rectype:
            args.rectype = args.rectype.split(',')
            for record_type in args.rectype:
                if record_type not in valid_record_types:
                    logging.fatal('invalid record type')
        elif args.rectype not in valid_record_types:
            logging.fatal('invalid record type')
        else:
            args.rectype = [args.rectype]
    
    if args.resolvers:
        if os.path.exists(args.resolvers):
            with open(args.resolvers, 'r') as file:
                dns_servers = [item.strip() for item in file.readlines() if item.strip()]
                logging.info(f'Loaded {len(dns_servers):,} DNS servers from file')
        else:
            logging.fatal('DNS servers file does not exist')
    else:
        dns_servers = urllib.request.urlopen('https://public-dns.info/nameservers.txt').read().decode().split('\n')
        logging.info(f'Loaded {len(dns_servers):,} DNS servers from public-dns.info')

    # Command line argument needed for this still
    if os.path.exists('random_subdomains.txt'):
        with open('random_subdomains.txt', 'r') as file:
            sub_domains = [item.strip() for item in file.readlines() if item.strip()]
            logging.info(f'Loaded {len(sub_domains):,} subdomains from file')
    else:
        logging.fatal('random_subdomains.txt is missing')
   
    dns_keys = dict()
    for dns_server in dns_servers:
        dns_keys[dns_server] = generate_subdomain(sub_domains)
    with open('dns_keys.txt', 'w') as file:
        json.dump(dns_keys, file)
    
    asyncio.run(main(args))