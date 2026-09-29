<?php

declare(strict_types=1);

namespace Demo;

function entry(): void
{
    helper();
    external_library_call();
}

function helper(): void
{
}

final class Service
{
    public function run(): void
    {
        $worker = new Worker();
        $worker->execute();
        Worker::staticExecute();
    }
}

final class Worker
{
    public function execute(): void
    {
        helper();
    }

    public static function staticExecute(): void
    {
    }
}
